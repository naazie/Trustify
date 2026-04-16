"""
IntelligenceLayer
─────────────────
Uses Google Gemini to enrich each finding with structured, pointwise output:

  • plain_english  : 2-sentence jargon-free explanation
  • what_it_means  : bullet-point list — what the vulnerability means in context
  • how_to_fix     : numbered, actionable remediation steps
  • why_it_matters : single sentence on business/security impact
  • impact_score   : float 0–10

The AI output is structured for easy reading — pointwise format, not walls of text.
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
You write clear, structured explanations that are easy to scan quickly.
You must respond ONLY with valid JSON. No markdown outside the JSON. No preamble."""

FINDING_PROMPT_TEMPLATE = """Analyze this security finding and return a JSON object with EXACTLY these keys:

- "plain_english": string — 2 clear sentences explaining what the vulnerability is, in plain language for a junior developer. No jargon.
- "what_it_means": array of 3-4 strings — each string is one short bullet point explaining the real-world implication or context of this finding.
- "how_to_fix": array of 3-5 strings — each string is one numbered, specific, actionable step to remediate this issue. Be concrete (include code patterns or library names where relevant).
- "why_it_matters": string — one sentence on the business/security impact if this is exploited.
- "impact_score": float 0.0–10.0 — exploitability × blast radius (10 = critical RCE/data breach; 0 = negligible).

Security Finding:
- Tool: {tool}
- Type: {finding_type}
- Subcategory: {subcategory}
- Rule ID: {rule_id}
- CWE: {cwe}
- Severity: {severity}
- Confidence: {confidence}
- File: {file_path} (line {line_start})
- Description: {description}
- Code Snippet: {code_snippet}

Respond ONLY with a JSON object. Example:
{{
  "plain_english": "This code passes user input directly into a SQL query without sanitization. An attacker can manipulate the query to read, modify, or delete database records.",
  "what_it_means": [
    "User-controlled data is injected into a raw SQL string",
    "No parameterized queries or ORM-level escaping is used",
    "An attacker can bypass authentication or exfiltrate all table data"
  ],
  "how_to_fix": [
    "Replace raw SQL concatenation with parameterized queries (e.g. cursor.execute('SELECT * FROM users WHERE id = %s', (user_id,)))",
    "Use an ORM like SQLAlchemy that handles escaping automatically",
    "Add input validation to reject unexpected characters before they reach DB layer",
    "Enable a WAF rule for SQLi patterns as a secondary defence"
  ],
  "why_it_matters": "Successful exploitation could allow an attacker to dump your entire database or bypass login.",
  "impact_score": 9.2
}}"""


class IntelligenceLayer:
    def __init__(self):
        if settings.gemini_api_key and settings.gemini_api_key not in ("", "your_gemini_api_key_here"):
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
            print("[Intelligence] ⚠️  No GEMINI_API_KEY — using structured fallbacks.")

    async def enrich_findings(self, findings: List[dict]) -> List[dict]:
        """Enrich findings with AI-generated structured fields (in-place)."""
        if not self.enabled:
            return [self._apply_fallback(f) for f in findings]

        for i in range(0, len(findings), BATCH_SIZE):
            batch = findings[i: i + BATCH_SIZE]
            for finding in batch:
                try:
                    enriched = await self._enrich_single(finding)
                    finding["plain_english"]  = enriched.get("plain_english", "")
                    finding["what_it_means"]  = enriched.get("what_it_means", [])
                    finding["how_to_fix"]     = enriched.get("how_to_fix", [])
                    finding["why_it_matters"] = enriched.get("why_it_matters", "")
                    # Keep legacy "remediation" field populated for backwards compat
                    finding["remediation"] = "\n".join(
                        f"• {s}" for s in finding["how_to_fix"]
                    )
                    finding["impact_score"] = float(enriched.get("impact_score", 5.0))
                except Exception as e:
                    print(f"[Intelligence] Error enriching {finding.get('rule_id')}: {e}")
                    self._apply_fallback(finding)

        return findings

    async def _enrich_single(self, finding: dict) -> dict:
        prompt = FINDING_PROMPT_TEMPLATE.format(
            tool=finding.get("tool", "unknown"),
            finding_type=finding.get("type", "SECURITY"),
            subcategory=finding.get("subcategory", "UNKNOWN"),
            rule_id=finding.get("rule_id", "unknown"),
            cwe=finding.get("cwe") or "N/A",
            severity=finding.get("severity", "warning"),
            confidence=finding.get("confidence", 0.7),
            file_path=finding.get("file_path", "unknown"),
            line_start=finding.get("line_start", 0),
            description=finding.get("description", "No description.")[:500],
            code_snippet=(finding.get("code_snippet") or "N/A")[:300],
        )

        response = await self.model.generate_content_async(prompt)
        text = response.text.strip()
        # Strip markdown fences if Gemini wraps output
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return json.loads(text)

    def _apply_fallback(self, finding: dict) -> dict:
        """
        Structured, pointwise fallback when Gemini is unavailable.
        Generates meaningful content based on finding type, subcategory, and severity.
        """
        severity  = finding.get("severity", "info")
        tool      = finding.get("tool", "unknown")
        rule_id   = finding.get("rule_id", "")
        ftype     = finding.get("type", "CODE_QUALITY")
        subcat    = finding.get("subcategory", "").replace("_", " ").title()
        cwe       = finding.get("cwe") or ""
        file_path = finding.get("file_path", "unknown")
        line      = finding.get("line_start", 0)

        score_map = {"critical": 8.5, "warning": 5.0, "info": 2.0}
        finding["impact_score"] = score_map.get(severity, 3.0)

        finding["plain_english"] = (
            f"A {severity}-severity {ftype.lower().replace('_', ' ')} issue "
            f"({subcat}) was detected by {tool} in {file_path} at line {line}. "
            f"{'CWE: ' + cwe + '. ' if cwe else ''}"
            f"Review the flagged code and apply the fix steps below."
        )

        # Type-specific what_it_means
        type_implications = {
            "SECURITY": [
                f"This {subcat} vulnerability could be exploited by an attacker",
                "The flagged code pattern is a known security anti-pattern",
                "If exploited, this may lead to data exposure or unauthorized access",
                f"Severity rated {severity} by {tool} static analysis",
            ],
            "SECRET": [
                "A credential, token, or private key appears hardcoded in the source",
                "Anyone with access to this repo (or its history) can read this secret",
                "Secrets in git history persist even after deletion from current files",
                "Rotate this credential immediately, regardless of whether it was used",
            ],
            "CODE_QUALITY": [
                f"Rule {rule_id} flags a code quality or maintainability issue",
                "This pattern may cause runtime errors or unexpected behaviour",
                "Code quality issues accumulate into technical debt over time",
                "Fixing this will improve reliability and future maintainability",
            ],
            "DEPENDENCY": [
                "A third-party dependency contains a known vulnerability",
                "This affects all users of this package version",
                "Check the CVE for public exploit availability",
                "Update or patch the dependency as soon as possible",
            ],
        }
        finding["what_it_means"] = type_implications.get(ftype, type_implications["SECURITY"])

        # Type-specific how_to_fix
        type_fixes = {
            "SECURITY": [
                f"Review line {line} in {file_path} and understand the data flow",
                "Apply input validation and output encoding at the appropriate layer",
                "Consult OWASP's cheatsheet for this vulnerability type",
                "Add a test case that confirms the fix prevents exploitation",
                "Add this check to your CI/CD pipeline (e.g. semgrep --config=auto)",
            ],
            "SECRET": [
                "Immediately revoke and rotate the exposed credential",
                "Remove the secret from source code — use environment variables instead",
                "Use a secrets manager (e.g. AWS Secrets Manager, HashiCorp Vault, Doppler)",
                "Run `git filter-repo` or BFG Repo Cleaner to purge the secret from git history",
                "Enable pre-commit hooks (e.g. gitleaks detect --pre-commit) to prevent recurrence",
            ],
            "CODE_QUALITY": [
                f"Open {file_path} at line {line} and review the flagged pattern",
                f"Address the {rule_id} violation per your linter's documentation",
                "Run the linter locally and fix all instances of this rule",
                "Add the rule to your CI/CD quality gate to prevent regression",
            ],
            "DEPENDENCY": [
                "Identify the exact package and version from the finding",
                "Check the NVD or Snyk database for CVE details and CVSS score",
                "Upgrade to the patched version specified in the security advisory",
                "If no patch exists, evaluate a replacement library or apply a workaround",
                "Add dependency scanning to your CI pipeline (e.g. `pip audit`, `npm audit`)",
            ],
        }
        finding["how_to_fix"] = type_fixes.get(ftype, type_fixes["SECURITY"])

        impact_sentences = {
            "critical": "If exploited, this could result in full system compromise, data breach, or service disruption.",
            "warning": "Exploitation is possible under certain conditions and could lead to partial data exposure or privilege escalation.",
            "info": "Low immediate risk, but leaving this unaddressed contributes to technical debt and may become exploitable in combination with other issues.",
        }
        finding["why_it_matters"] = impact_sentences.get(severity, impact_sentences["warning"])

        # Backwards-compat remediation field
        finding["remediation"] = "\n".join(f"• {s}" for s in finding["how_to_fix"])

        return finding
