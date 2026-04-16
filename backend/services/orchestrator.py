"""
JobOrchestrator
───────────────
The core engine of Trustify.

Flow:
  1. Update scan status → "running"
  2. Ingest source code (clone / extract)
  3. Detect languages
  4. Determine which tools to run based on languages
  5. Run each tool in a Docker sibling container (volume-mounted workspace)
  6. Collect raw JSON outputs
  7. Normalize findings via NormalizationEngine
  8. Enrich findings via IntelligenceLayer (Gemini)
  9. Persist findings to MongoDB
  10. Update scan summary + status → "complete"
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from bson import ObjectId

from config import settings
from services.ingestion import IngestionService
from services.normalizer import NormalizationEngine
from services.intelligence import IntelligenceLayer
from tools.semgrep_runner import run_semgrep
from tools.gitleaks_runner import run_gitleaks
from tools.pylint_runner import run_pylint
from tools.eslint_runner import run_eslint


class JobOrchestrator:
    def __init__(self, db):
        self.db = db
        self.ingestion = IngestionService()
        self.normalizer = NormalizationEngine()
        self.intelligence = IntelligenceLayer()

    # ─── Main Entry Point ─────────────────────────────────────────────────────
    async def run_scan(
        self,
        scan_id: str,
        source_type: str,
        source_url: Optional[str],
        file_bytes: Optional[bytes],
        filename: Optional[str],
    ):
        print(f"\n{'='*60}")
        print(f"[Orchestrator] Starting scan {scan_id}")
        print(f"{'='*60}")

        workspace: Optional[Path] = None
        try:
            # 1. Mark as running
            await self._update_scan(scan_id, {"status": "running"})

            # 2. Ingest
            if source_type == "github":
                workspace = self.ingestion.ingest_github(source_url, scan_id)
            else:
                workspace = self.ingestion.ingest_zip(file_bytes, scan_id)

            # 3. Detect languages
            languages = self.ingestion.detect_languages(workspace)
            await self._update_scan(scan_id, {"languages": languages})

            # 4. Determine tools
            tools_to_run = self._select_tools(languages)
            print(f"[Orchestrator] Tools selected: {tools_to_run}")

            # 5 & 6. Run tools concurrently & collect raw outputs
            loop = asyncio.get_event_loop()
            raw_results = await self._run_tools_parallel(tools_to_run, workspace, loop)

            await self._update_scan(scan_id, {"tools_run": tools_to_run})

            # 7. Normalize
            all_findings: List[dict] = []
            for tool, raw in raw_results.items():
                normalized = self.normalizer.normalize(tool, raw, scan_id)
                all_findings.extend(normalized)
                print(f"[Orchestrator] {tool}: {len(normalized)} findings normalized")

            # 8. AI enrichment
            print(f"[Orchestrator] Enriching {len(all_findings)} findings with AI...")
            all_findings = await self.intelligence.enrich_findings(all_findings)

            # 9. Persist findings
            if all_findings:
                await self.db.findings.insert_many(all_findings)
            print(f"[Orchestrator] Saved {len(all_findings)} findings to MongoDB")

            # 10. Compute summary & mark complete
            summary = self._compute_summary(all_findings)
            await self._update_scan(scan_id, {
                "status": "complete",
                "completed_at": datetime.utcnow(),
                "summary": summary,
            })

            print(f"[Orchestrator] ✅ Scan {scan_id} complete — {summary}")

        except Exception as e:
            print(f"[Orchestrator] ❌ Scan {scan_id} failed: {e}")
            await self._update_scan(scan_id, {
                "status": "failed",
                "completed_at": datetime.utcnow(),
                "error_message": str(e),
            })
        finally:
            # DEBUG MODE: cleanup disabled so _debug_* files are readable on host.
            # Re-enable when done debugging:
            #   if workspace:
            #       self.ingestion.cleanup(scan_id)
            if workspace:
                print(f"[Orchestrator] DEBUG: workspace kept at {workspace} — inspect _debug_* files then delete manually")

    # ─── Tool Selection ───────────────────────────────────────────────────────
    def _select_tools(self, languages: List[str]) -> List[str]:
        tools = ["semgrep", "gitleaks"]  # Always run these two
        lang_set = set(languages)
        if {"python"}.intersection(lang_set):
            tools.append("pylint")
        if {"javascript", "typescript"}.intersection(lang_set):
            tools.append("eslint")
        return tools

    # ─── Parallel Tool Execution ──────────────────────────────────────────────
    async def _run_tools_parallel(
        self,
        tools: List[str],
        workspace: Path,
        loop: asyncio.AbstractEventLoop,
    ) -> dict:
        TOOL_RUNNERS = {
            "semgrep": run_semgrep,
            "gitleaks": run_gitleaks,
            "pylint": run_pylint,
            "eslint": run_eslint,
        }

        async def run_one(tool: str):
            runner = TOOL_RUNNERS.get(tool)
            if not runner:
                return tool, {}
            print(f"[Orchestrator] ▶ Starting {tool}...")
            result = await loop.run_in_executor(None, runner, str(workspace))
            print(f"[Orchestrator] ✓ {tool} finished")
            return tool, result

        tasks = [run_one(t) for t in tools]
        results = await asyncio.gather(*tasks)

        raw_results = {tool: data for tool, data in results}
        return raw_results

    # ─── Summary ─────────────────────────────────────────────────────────────
    def _compute_summary(self, findings: List[dict]) -> dict:
        summary = {"critical": 0, "warning": 0, "info": 0, "total": 0}
        for f in findings:
            sev = f.get("severity", "info")
            if sev in summary:
                summary[sev] += 1
            summary["total"] += 1
        return summary

    # ─── DB Helper ────────────────────────────────────────────────────────────
    async def _update_scan(self, scan_id: str, updates: dict):
        await self.db.scans.update_one(
            {"_id": ObjectId(scan_id)},
            {"$set": updates},
        )