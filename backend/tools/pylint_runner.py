"""
Pylint Docker Runner
─────────────────────
Runs Pylint on Python files in the workspace.
Returns a list of message dicts in Pylint's JSON format.
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


def run_pylint(workspace_path: str) -> list:
    """Execute Pylint natively and return parsed JSON message list."""
    scan_id = Path(workspace_path).name

    cmd = [
        "pylint",
        "--output-format=json",
        "--recursive=y",
        workspace_path,
    ]

    print(f"[Pylint] Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        _save_debug(workspace_path, "pylint", stdout, stderr, result.returncode)

        print(f"[Pylint] returncode={result.returncode}")
        if stderr:
            print(f"[Pylint] stderr (first 800 chars):\n{stderr[:800]}")

        if not stdout:
            print("[Pylint] stdout was empty")
            return []

        data = json.loads(stdout)
        count = len(data) if isinstance(data, list) else 0
        print(f"[Pylint] Found {count} messages")
        return data if isinstance(data, list) else []

    except subprocess.TimeoutExpired:
        print("[Pylint] ⚠️  Timeout — skipping")
        return []
    except json.JSONDecodeError as e:
        print(f"[Pylint] ⚠️  JSON parse error: {e}")
        return []
    except FileNotFoundError:
        print("[Pylint] ⚠️  pylint command not found")
        raise RuntimeError("[Pylint] pylint executable not found. Ensure it is installed natively.")
    except Exception as e:
        raise RuntimeError(f"[Pylint] Native run failed: {e}")