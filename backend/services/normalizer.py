"""
NormalizationEngine
────────────────────
Converts raw tool output JSON into the unified Finding schema.

Unified schema (matches the image spec):
  {
    "type":        "SECURITY" | "CODE_QUALITY" | "SECRET" | "DEPENDENCY",
    "subcategory": e.g. "SQL_INJECTION", "HARDCODED_SECRET", "UNUSED_VARIABLE"
    "severity":    "critical" | "warning" | "info",
    "confidence":  float 0.0–1.0,
    "file":        "relative/path/to/file.js",
    "line":        87,
    "tool":        "semgrep" | "gitleaks" | "pylint" | "eslint"
  }

Plus enrichment fields:
  description, code_snippet, cwe, rule_id, title,
  plain_english (AI), remediation (AI, pointwise), impact_score (AI)

De-duplication via SHA-256 hash of (file_path + rule_id + line_start).
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from typing import Any, Dict, List, Optional


# ─── Severity Maps ────────────────────────────────────────────────────────────
SEVERITY_MAP: dict[str, str] = {
    "critical": "critical", "error": "critical",
    "high": "critical",     "blocker": "critical",
    "warning": "warning",   "medium": "warning",
    "major": "warning",     "warn": "warning",
    "info": "info",         "low": "info",
    "style": "info",        "convention": "info",
    "refactor": "info",     "minor": "info",
    "note": "info",         "suggestion": "info",
}

# ESLint severity codes → string
ESLINT_SEV_MAP = {2: "critical", 1: "warning", 0: "info"}

# Confidence by severity (heuristic baseline, AI can override)
SEVERITY_CONFIDENCE: dict[str, float] = {
    "critical": 0.90,
    "warning": 0.70,
    "info": 0.50,
}

# Semgrep rule prefixes → finding type
SEMGREP_TYPE_MAP: dict[str, str] = {
    "security": "SECURITY",
    "injection": "SECURITY",
    "xss": "SECURITY",
    "ssrf": "SECURITY",
    "sqli": "SECURITY",
    "rce": "SECURITY",
    "auth": "SECURITY",
    "crypto": "SECURITY",
    "taint": "SECURITY",
    "secret": "SECRET",
    "token": "SECRET",
    "key": "SECRET",
    "password": "SECRET",
    "correctness": "CODE_QUALITY",
    "performance": "CODE_QUALITY",
    "best-practice": "CODE_QUALITY",
    "maintainability": "CODE_QUALITY",
}

# ESLint rule_id → subcategory lookup
ESLINT_SUBCATEGORY_MAP: dict[str, str] = {
    "no-eval": "EVAL_INJECTION",
    "no-implied-eval": "EVAL_INJECTION",
    "no-new-func": "EVAL_INJECTION",
    "no-script-url": "XSS",
    "no-proto": "PROTOTYPE_POLLUTION",
    "no-extend-native": "PROTOTYPE_POLLUTION",
    "security/detect-object-injection": "OBJECT_INJECTION",
    "security/detect-non-literal-regexp": "REGEX_INJECTION",
    "security/detect-non-literal-fs-filename": "PATH_TRAVERSAL",
    "security/detect-child-process": "COMMAND_INJECTION",
    "security/detect-disable-mustache-escape": "XSS",
    "security/detect-eval-with-expression": "EVAL_INJECTION",
    "security/detect-no-csrf-before-method-override": "CSRF",
    "security/detect-possible-timing-attacks": "TIMING_ATTACK",
    "security/detect-pseudoRandomBytes": "WEAK_RANDOM",
    "security/detect-unsafe-regex": "REDOS",
    "no-alert": "POOR_PRACTICE",
    "no-unsafe-finally": "CONTROL_FLOW",
    "no-global-assign": "GLOBAL_MUTATION",
    "no-unreachable": "DEAD_CODE",
    "no-unused-vars": "UNUSED_VARIABLE",
    "no-undef": "UNDEFINED_VARIABLE",
    "@typescript-eslint/no-explicit-any": "TYPE_SAFETY",
}


def _map_severity(raw: str) -> str:
    return SEVERITY_MAP.get(str(raw).lower(), "info")


def _dedup_key(file_path: str, rule_id: str, line_start: int) -> str:
    raw = f"{file_path}:{rule_id}:{line_start}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _semgrep_type_and_subcategory(rule_id: str, metadata: dict) -> tuple[str, str]:
    """Derive (type, subcategory) from a Semgrep rule ID and metadata."""
    rule_lower = rule_id.lower()

    # Check metadata CWE/category first
    cwe = metadata.get("cwe", "")
    if isinstance(cwe, list):
        cwe = cwe[0] if cwe else ""
    cwe = str(cwe).upper()

    # CWE → type mapping
    cwe_type_map = {
        "CWE-89": ("SECURITY", "SQL_INJECTION"),
        "CWE-79": ("SECURITY", "XSS"),
        "CWE-78": ("SECURITY", "COMMAND_INJECTION"),
        "CWE-22": ("SECURITY", "PATH_TRAVERSAL"),
        "CWE-327": ("SECURITY", "WEAK_CRYPTO"),
        "CWE-798": ("SECRET", "HARDCODED_SECRET"),
        "CWE-502": ("SECURITY", "DESERIALIZATION"),
        "CWE-918": ("SECURITY", "SSRF"),
        "CWE-611": ("SECURITY", "XXE"),
        "CWE-94": ("SECURITY", "CODE_INJECTION"),
        "CWE-601": ("SECURITY", "OPEN_REDIRECT"),
        "CWE-200": ("SECURITY", "INFO_DISCLOSURE"),
        "CWE-287": ("SECURITY", "AUTH_BYPASS"),
        "CWE-352": ("SECURITY", "CSRF"),
    }
    for cwe_id, (t, sub) in cwe_type_map.items():
        if cwe_id in cwe:
            return t, sub

    # Rule ID keyword scan
    for keyword, finding_type in SEMGREP_TYPE_MAP.items():
        if keyword in rule_lower:
            # Subcategory from last segment of rule ID
            subcategory = rule_id.split(".")[-1].upper().replace("-", "_")[:30]
            return finding_type, subcategory

    # Default
    subcategory = rule_id.split(".")[-1].upper().replace("-", "_")[:30]
    return "CODE_QUALITY", subcategory


def _gitleaks_confidence(rule_id: str, match: str) -> float:
    """Gitleaks confidence varies by rule specificity."""
    high_confidence_rules = {
        "aws-access-token", "aws-secret-key", "github-pat", "github-fine-grained-pat",
        "stripe-access-token", "private-key", "pem-private-key", "ssh-private-key",
        "twilio-api-key", "sendgrid-api-token", "slack-bot-token",
    }
    if rule_id.lower() in high_confidence_rules:
        return 0.97
    if len(match) > 20:  # longer matches = more specific pattern
        return 0.85
    return 0.75


def normalize_semgrep(raw: Dict[str, Any], scan_id: str) -> List[dict]:
    results = raw.get("results", [])
    findings = []
    seen = set()

    for r in results:
        file_path = r.get("path", "unknown")
        # Normalise to relative path
        for prefix in ("/src/", "/path/"):
            if file_path.startswith(prefix):
                file_path = file_path[len(prefix):]

        rule_id = r.get("check_id", "semgrep-unknown")
        line_start = r.get("start", {}).get("line", 0)
        line_end = r.get("end", {}).get("line", line_start)
        extra = r.get("extra", {})
        severity_raw = extra.get("severity", "warning")
        severity = _map_severity(severity_raw)
        description = extra.get("message", "No description provided.")
        code_snippet = extra.get("lines", "")
        metadata = extra.get("metadata", {})

        cwe = None
        if "cwe" in metadata:
            cwe_raw = metadata["cwe"]
            cwe = cwe_raw[0] if isinstance(cwe_raw, list) else str(cwe_raw)

        finding_type, subcategory = _semgrep_type_and_subcategory(rule_id, metadata)

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "scan_id": scan_id,
            "tool": "semgrep",
            # ── New unified schema fields ──
            "type": finding_type,
            "subcategory": subcategory,
            "confidence": SEVERITY_CONFIDENCE.get(severity, 0.70),
            # ── Standard fields ──
            "severity": severity,
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
    if not raw or not isinstance(raw, list):
        return []

    findings = []
    seen = set()

    for r in raw:
        file_path = r.get("File", "unknown")
        for prefix in ("/src/", "/path/"):
            if file_path.startswith(prefix):
                file_path = file_path[len(prefix):]

        rule_id = r.get("RuleID", "gitleaks-unknown")
        line_start = r.get("StartLine", 0)
        line_end = r.get("EndLine", line_start)
        match = r.get("Match", "")
        secret = r.get("Secret", match)

        # Determine if from history scan (has Commit field)
        commit = r.get("Commit", "")
        commits = r.get("_commits", [])
        if commit and commit not in commits:
            commits = [commit] + commits

        scan_mode = r.get("_scan_mode", "working_tree")

        # Build description with commit provenance
        if commits:
            commit_info = f"Found in {len(commits)} commit(s): {', '.join(c[:8] for c in commits[:3])}"
            if len(commits) > 3:
                commit_info += f" (+{len(commits) - 3} more)"
            description = (
                f"Secret leaked in commit history — rule: {rule_id}. "
                f"Pattern: '{secret[:20]}...' " if len(secret) > 20
                else f"Pattern: '{secret}' "
            )
            description = (
                f"{'[HISTORY] ' if scan_mode == 'git_log' else ''}"
                f"Secret detected — rule: {rule_id}. "
                + (f"Match: '{secret[:20]}...'" if len(secret) > 20 else f"Match: '{secret}'")
                + (f" | {commit_info}" if commits else "")
            )
        else:
            description = (
                f"Secret detected — rule: {rule_id}. "
                + (f"Match: '{secret[:20]}...'" if len(secret) > 20 else f"Match: '{secret}'")
            )

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        # Categorize secret type
        rule_lower = rule_id.lower()
        if any(x in rule_lower for x in ("aws", "azure", "gcp", "google", "cloud")):
            subcategory = "CLOUD_CREDENTIAL"
        elif any(x in rule_lower for x in ("key", "api-key", "apikey")):
            subcategory = "API_KEY"
        elif any(x in rule_lower for x in ("password", "passwd", "pwd")):
            subcategory = "HARDCODED_PASSWORD"
        elif any(x in rule_lower for x in ("token", "pat", "jwt")):
            subcategory = "AUTH_TOKEN"
        elif any(x in rule_lower for x in ("private-key", "pem", "ssh", "rsa")):
            subcategory = "PRIVATE_KEY"
        else:
            subcategory = "HARDCODED_SECRET"

        findings.append({
            "scan_id": scan_id,
            "tool": "gitleaks",
            "type": "SECRET",
            "subcategory": subcategory,
            "confidence": _gitleaks_confidence(rule_id, secret),
            "severity": "critical",
            "rule_id": rule_id,
            "cwe": "CWE-798",
            "title": f"Leaked Secret — {rule_id.replace('-', ' ').title()}",
            "description": description,
            "file_path": file_path,
            "line_start": line_start,
            "line_end": line_end,
            "code_snippet": match,
            "commit_history": commits if commits else None,
            "found_in_history": scan_mode == "git_log",
            "created_at": datetime.utcnow(),
        })
    return findings


def normalize_pylint(raw: Any, scan_id: str) -> List[dict]:
    if not raw or not isinstance(raw, list):
        return []

    findings = []
    seen = set()

    # Pylint type codes → finding type
    pylint_type_map = {
        "error": "CODE_QUALITY",
        "warning": "CODE_QUALITY",
        "convention": "CODE_QUALITY",
        "refactor": "CODE_QUALITY",
        # Security-relevant pylint codes
        "W0611": "CODE_QUALITY",   # unused-import
        "W0612": "CODE_QUALITY",   # unused-variable
        "E1101": "CODE_QUALITY",   # member-error
        "W0703": "SECURITY",       # broad-except (can hide errors)
        "W0702": "SECURITY",       # bare-except
        "W0106": "SECURITY",       # expression-not-assigned
    }

    for r in raw:
        file_path = r.get("path", "unknown")
        for prefix in ("/src/", "/path/"):
            if file_path.startswith(prefix):
                file_path = file_path[len(prefix):]

        rule_id = r.get("message-id", "pylint-unknown")
        line_start = r.get("line", 0)
        line_end = r.get("endLine", line_start) or line_start
        severity_raw = r.get("type", "warning")
        severity = _map_severity(severity_raw)
        description = r.get("message", "No description provided.")
        symbol = r.get("symbol", rule_id)
        obj = r.get("obj", "")

        # Subcategory from pylint symbol (e.g. "unused-import" → "UNUSED_IMPORT")
        subcategory = symbol.upper().replace("-", "_")[:30]
        finding_type = pylint_type_map.get(rule_id, pylint_type_map.get(severity_raw, "CODE_QUALITY"))

        title = f"{rule_id} ({symbol})"
        if obj:
            title += f" in {obj}"

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        findings.append({
            "scan_id": scan_id,
            "tool": "pylint",
            "type": finding_type,
            "subcategory": subcategory,
            "confidence": SEVERITY_CONFIDENCE.get(severity, 0.60),
            "severity": severity,
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


def normalize_eslint(raw: Any, scan_id: str) -> List[dict]:
    """
    ESLint returns a flat list of messages (already pre-processed by eslint_runner).
    Each message: { filePath, ruleId, message, severity(int), line, endLine, column }
    """
    if not raw or not isinstance(raw, list):
        return []

    findings = []
    seen = set()

    for r in raw:
        file_path = r.get("filePath", "unknown")
        rule_id = r.get("ruleId") or "eslint-unknown"
        line_start = r.get("line", 0)
        line_end = r.get("endLine", line_start) or line_start
        severity_int = r.get("severity", 1)
        severity = ESLINT_SEV_MAP.get(severity_int, "warning")
        description = r.get("message", "No description provided.")

        # Type and subcategory
        rule_lower = rule_id.lower()
        subcategory = ESLINT_SUBCATEGORY_MAP.get(rule_id, rule_id.upper().replace("/", "_").replace("-", "_")[:30])

        if any(x in rule_lower for x in ("security/", "eval", "proto", "csrf", "timing", "random", "regex", "child_process")):
            finding_type = "SECURITY"
        elif any(x in rule_lower for x in ("no-unused", "no-undef", "no-unreachable")):
            finding_type = "CODE_QUALITY"
        else:
            finding_type = "CODE_QUALITY"

        # CWE for known security rules
        cwe_map = {
            "no-eval": "CWE-94",
            "no-implied-eval": "CWE-94",
            "no-new-func": "CWE-94",
            "no-script-url": "CWE-79",
            "security/detect-object-injection": "CWE-94",
            "security/detect-non-literal-fs-filename": "CWE-22",
            "security/detect-child-process": "CWE-78",
            "security/detect-disable-mustache-escape": "CWE-79",
            "security/detect-no-csrf-before-method-override": "CWE-352",
            "security/detect-pseudoRandomBytes": "CWE-338",
            "security/detect-unsafe-regex": "CWE-185",
            "no-proto": "CWE-1321",
        }
        cwe = cwe_map.get(rule_id)

        key = _dedup_key(file_path, rule_id, line_start)
        if key in seen:
            continue
        seen.add(key)

        title = rule_id.replace("/", " › ").replace("-", " ").replace("_", " ").title()

        findings.append({
            "scan_id": scan_id,
            "tool": "eslint",
            "type": finding_type,
            "subcategory": subcategory,
            "confidence": SEVERITY_CONFIDENCE.get(severity, 0.70),
            "severity": severity,
            "rule_id": rule_id,
            "cwe": cwe,
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
        elif tool == "eslint":
            return normalize_eslint(raw, scan_id)
        else:
            print(f"[Normalizer] Unknown tool: {tool}")
            return []
