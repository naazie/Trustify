"""
Semgrep Docker Runner
──────────────────────
Runs Semgrep inside a Docker sibling container.
Volume-mounts the workspace as read-only /src.
Returns parsed JSON findings dict.
"""
from __future__ import annotations

import json
import subprocess
import os
from pathlib import Path

from config import settings

def _save_debug(workspace_path: str, tool: str, stdout: str, stderr: str, returncode: int):
    """Save raw tool output into the workspace folder (host-mounted, so readable on host)."""
    base = os.path.join(workspace_path, f"_debug_{tool}")
    with open(f"{base}_stdout.json", "w") as f:
        f.write(stdout or "(empty)")
    with open(f"{base}_stderr.txt", "w") as f:
        f.write(f"returncode: {returncode}\n\n{stderr or '(empty)'}")
    print(f"[{tool.upper()}] Debug files: {base}_stdout.json  (host: /tmp/trustify_workspaces/{os.path.basename(workspace_path)}/_debug_{tool}_*)")


def run_semgrep(workspace_path: str) -> dict:
    """Execute Semgrep natively and return parsed JSON output."""
    scan_id = Path(workspace_path).name

    cmd = [
        "semgrep",
        "--config=auto",
        "--json",
        "--no-git-ignore",
        "--timeout=60",
        workspace_path,
    ]

    print(f"[Semgrep] Running: {' '.join(cmd)}")

    try:
        # We allow semgrep to use its cache path in /tmp by default natively
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env={**os.environ, "SEMGREP_RULES_CACHE_PATH": "/tmp"}
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        _save_debug(workspace_path, "semgrep", stdout, stderr, result.returncode)

        print(f"[Semgrep] returncode={result.returncode}")
        if stderr:
            print(f"[Semgrep] stderr (first 800 chars):\n{stderr[:800]}")

        if not stdout:
            print("[Semgrep] stdout was empty")
            return {"results": []}

        data = json.loads(stdout)
        count = len(data.get("results", []))
        print(f"[Semgrep] Found {count} results")
        return data

    except subprocess.TimeoutExpired:
        print("[Semgrep] ⚠️  Timeout — skipping")
        return {"results": []}
    except json.JSONDecodeError as e:
        print(f"[Semgrep] ⚠️  JSON parse error: {e}")
        return {"results": []}
    except FileNotFoundError:
        print("[Semgrep] ⚠️  semgrep command not found")
        raise RuntimeError("[Semgrep] semgrep executable not found. Ensure it is installed natively.")
    except Exception as e:
        raise RuntimeError(f"[Semgrep] Native run failed: {e}")