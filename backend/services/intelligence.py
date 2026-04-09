"""
IntelligenceLayer
─────────────────
Uses Google Gemini to enrich each finding with:
  • plain_english : jargon-free 2-sentence explanation
  • remediation   : 3 actionable bullet-point fix steps
  • impact_score  : float 0–10 (exploitability × impact)

Findings are processed in batches of 8 to stay within token limits.
"""
from __future__ import annotations

import json
import re
from typing import List

import google.generativeai as genai

from config import settings


GEMINI_MODEL = "gemini-2.0-flash"
BATCH_SIZE = 8

SYSTEM_PROMPT = """You are a senior application security engineer helping developers understand and fix security vulnerabilities.
You must respond ONLY with valid JSON. No markdown, no explanation outside the JSON structure."""

FINDING_PROMPT_TEMPLATE = """Analyze the following security finding and return a JSON object with exactly these keys:
- "plain_english": A clear, jargon-free 2-sentence explanation of the security risk for a junior developer.
- "remediation": A string with exactly 3 actionable bullet points (using • as bullet character) explaining how to fix the issue.
- "impact_score": A float between 0 and 10 representing the severity (10 = most critical, exploitable; 0 = negligible).

Security Finding:
- Tool: {tool}
- Rule ID: {rule_id}
- CWE: {cwe}
- Severity: {severity}
- File: {file_path} (line {line_start})
- Description: {description}
- Code Snippet: {code_snippet}

Respond ONLY with a JSON object. Example format:
{{"plain_english": "...", "remediation": "• Step 1\\n• Step 2\\n• Step 3", "impact_score": 7.5}}"""


class IntelligenceLayer:
    def __init__(self):
        if settings.gemini_api_key and settings.gemini_api_key != "your_gemini_api_key_here":
            genai.configure(api_key=settings.gemini_api_key)
            self.model = genai.GenerativeModel(
                model_name=GEMINI_MODEL,
                system_instruction=SYSTEM_PROMPT,
            )
            self.enabled = True
            print("[Intelligence] Gemini AI layer enabled ✅")
        else:
            self.model = None
            self.enabled = False
            print("[Intelligence] ⚠️  No GEMINI_API_KEY — AI enrichment disabled, using fallbacks.")

    async def enrich_findings(self, findings: List[dict]) -> List[dict]:
        """Enrich a list of findings with AI-generated fields (in-place)."""
        if not self.enabled:
            return [self._apply_fallback(f) for f in findings]

        # Process in batches
        for i in range(0, len(findings), BATCH_SIZE):
            batch = findings[i : i + BATCH_SIZE]
            for finding in batch:
                try:
                    enriched = await self._enrich_single(finding)
                    finding["plain_english"] = enriched.get("plain_english", "")
                    finding["remediation"] = enriched.get("remediation", "")
                    finding["impact_score"] = float(enriched.get("impact_score", 5.0))
                except Exception as e:
                    print(f"[Intelligence] Error enriching finding {finding.get('rule_id')}: {e}")
                    self._apply_fallback(finding)

        return findings

    async def _enrich_single(self, finding: dict) -> dict:
        prompt = FINDING_PROMPT_TEMPLATE.format(
            tool=finding.get("tool", "unknown"),
            rule_id=finding.get("rule_id", "unknown"),
            cwe=finding.get("cwe") or "N/A",
            severity=finding.get("severity", "warning"),
            file_path=finding.get("file_path", "unknown"),
            line_start=finding.get("line_start", 0),
            description=finding.get("description", "No description.")[:500],
            code_snippet=(finding.get("code_snippet") or "N/A")[:300],
        )

        response = await self.model.generate_content_async(prompt)
        text = response.text.strip()

        # Strip markdown code fences if Gemini wraps in ```json
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

        return json.loads(text)

    def _apply_fallback(self, finding: dict) -> dict:
        """Apply rule-based fallbacks when Gemini is unavailable."""
        severity = finding.get("severity", "info")
        tool = finding.get("tool", "unknown")
        rule_id = finding.get("rule_id", "")

        score_map = {"critical": 8.5, "warning": 5.0, "info": 2.0}
        finding["impact_score"] = score_map.get(severity, 3.0)
        finding["plain_english"] = (
            f"A {severity}-level security issue was identified by {tool} "
            f"(rule: {rule_id}). Review the flagged code and apply the recommended fix."
        )
        finding["remediation"] = (
            "• Review the flagged code location carefully.\n"
            "• Consult OWASP guidelines for this vulnerability type.\n"
            "• Add this rule to your CI/CD pipeline to prevent future occurrences."
        )
        return finding
