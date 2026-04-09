"""
NormalizationEngine
────────────────────
Converts raw tool output JSON into the unified Finding schema.
Applies:
  • Severity mapping (tool-native → critical/warning/info)
  • De-duplication via SHA-256 hash of (file_path + rule_id + line_start)
  • Schema normalization per tool
"""
from __future__ import annotations

import hashlib
from datetime import datetime
from typing import Any, Dict, List


# ─── Severity Maps ────────────────────────────────────────────────────────────
SEVERITY_MAP: dict[str, str] = {
    # Common high
    "critical": "critical",
    "error": "critical",
    "high": "critical",
    "blocker": "critical",
    # Common medium
    "warning": "warning",
    "medium": "warning",
    "major": "warning",
    # Common low / info
    "info": "info",
    "low": "info",
    "style": "info",
    "convention": "info",
    "refactor": "info",
    "minor": "info",
    "note": "info",
}


def _map_severity(raw: str) -> str:
    return SEVERITY_MAP.get(raw.lower(), "info")


def _dedup_key(file_path: str, rule_id: str, line_start: int) -> str:
    raw = f"{file_path}:{rule_id}:{line_start}"
    return hashlib.sha256(raw.encode()).hexdigest()


# ─── Normalizers ─────────────────────────────────────────────────────────────

def normalize_semgrep(raw: Dict[str, Any], scan_id: str) -> List[dict]:
    results = raw.get("results", [])
    findings = []
    seen = set()

    for r in results:
        file_path = r.get("path", "unknown")
        rule_id = r.get("check_id", "semgrep-unknown")
        line_start = r.get("start", {}).get("line", 0)
        line_end = r.get("end", {}).get("line", line_start)
        extra = r.get("extra", {})
        severity_raw = extra.get("severity", "warning")
        description = extra.get("message", "No description provided.")
        code_snippet = extra.get("lines", "")
        metadata = extra.get("metadata", {})
        cwe = None
        if "cwe" in metadata:
            cwe_raw = metadata["cwe"]
            cwe = cwe_raw[0] if isinstance(cwe_raw, list) else str(cwe_raw)

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "scan_id": scan_id,
            "tool": "semgrep",
            "severity": _map_severity(severity_raw),
            "rule_id": rule_id,
            "cwe": cwe,
            "title": rule_id.split(".")[-1].replace("-", " ").title(),
            "description": description,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code_snippet": code_snippet,
            "created_at": datetime.utcnow(),
        })
    return findings


def normalize_gitleaks(raw: Any, scan_id: str) -> List[dict]:
    # Gitleaks returns a JSON array (or null)
    if not raw or not isinstance(raw, list):
        return []

    findings = []
    seen = set()

    for r in raw:
        file_path = r.get("File", "unknown")
        rule_id = r.get("RuleID", "gitleaks-unknown")
        line_start = r.get("StartLine", 0)
        line_end = r.get("EndLine", line_start)
        secret = r.get("Secret", "")
        description = (
            f"Potential secret detected — rule: {rule_id}. "
            f"Match: '{secret[:20]}...'" if len(secret) > 20 else f"Match: '{secret}'"
        )

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "scan_id": scan_id,
            "tool": "gitleaks",
            "severity": "critical",   # All secrets are critical
            "rule_id": rule_id,
            "cwe": "CWE-798",         # Use of Hard-coded Credentials
            "title": f"Leaked Secret — {rule_id.replace('-', ' ').title()}",
            "description": description,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code_snippet": r.get("Match", ""),
            "created_at": datetime.utcnow(),
        })
    return findings


def normalize_pylint(raw: Any, scan_id: str) -> List[dict]:
    if not raw or not isinstance(raw, list):
        return []

    findings = []
    seen = set()

    for r in raw:
        file_path = r.get("path", "unknown")
        rule_id = r.get("message-id", "pylint-unknown")
        line_start = r.get("line", 0)
        line_end = r.get("endLine", line_start) or line_start
        severity_raw = r.get("type", "warning")
        description = r.get("message", "No description provided.")
        module = r.get("module", "")
        obj = r.get("obj", "")
        title_parts = [rule_id]
        if obj:
            title_parts.append(f"in {obj}")
        title = " ".join(title_parts)

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "scan_id": scan_id,
            "tool": "pylint",
            "severity": _map_severity(severity_raw),
            "rule_id": rule_id,
            "cwe": None,
            "title": title,
            "description": description,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code_snippet": None,
            "created_at": datetime.utcnow(),
        })
    return findings


class NormalizationEngine:
    def normalize(self, tool: str, raw: Any, scan_id: str) -> List[dict]:
        if tool == "semgrep":
            return normalize_semgrep(raw, scan_id)
        elif tool == "gitleaks":
            return normalize_gitleaks(raw, scan_id)
        elif tool == "pylint":
            return normalize_pylint(raw, scan_id)
        else:
            print(f"[Normalizer] Unknown tool: {tool}")
            return []
