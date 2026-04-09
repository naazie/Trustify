"""
Gitleaks Docker Runner
───────────────────────
Detects secrets, API keys, credentials, and tokens in source code.
Returns a list of leak findings (JSON array).
"""
from __future__ import annotations

import json
import subprocess
from config import settings


def run_gitleaks(workspace_path: str) -> list:
    """Execute Gitleaks via Docker and return parsed JSON findings list."""

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{workspace_path}:/path:ro",
        settings.gitleaks_image,
        "detect",
        "--source=/path",
        "--report-format=json",
        "--report-path=/dev/stdout",
        "--no-git",
        "--exit-code=0",    # Don't fail on findings
    ]

    print(f"[Gitleaks] Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )
        stdout = result.stdout.strip()
        if not stdout or stdout == "null":
            print("[Gitleaks] No secrets found")
            return []

        data = json.loads(stdout)
        count = len(data) if isinstance(data, list) else 0
        print(f"[Gitleaks] Found {count} potential secrets")
        return data if isinstance(data, list) else []

    except subprocess.TimeoutExpired:
        print("[Gitleaks] ⚠️  Timeout — skipping")
        return []
    except json.JSONDecodeError as e:
        print(f"[Gitleaks] ⚠️  JSON parse error: {e}")
        return []
    except FileNotFoundError:
        print("[Gitleaks] ⚠️  Docker not found — skipping")
        return []
