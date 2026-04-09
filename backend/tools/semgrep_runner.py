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
import tempfile
import os
from pathlib import Path

from config import settings


def run_semgrep(workspace_path: str) -> dict:
    """Execute Semgrep via Docker and return parsed JSON output."""
    output_file = os.path.join(workspace_path, "_semgrep_output.json")

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{workspace_path}:/src:ro",
        settings.semgrep_image,
        "semgrep",
        "--config=auto",
        "--json",
        "--no-git-ignore",
        "--timeout=60",
        "/src",
    ]

    print(f"[Semgrep] Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        # Semgrep exits 1 on findings, 0 on no findings
        stdout = result.stdout.strip()
        if not stdout:
            print(f"[Semgrep] No output. stderr: {result.stderr[:500]}")
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
        print("[Semgrep] ⚠️  Docker not found — running semgrep natively if available")
        return _run_semgrep_native(workspace_path)


def _run_semgrep_native(workspace_path: str) -> dict:
    """Fallback: run semgrep natively (if installed on host)."""
    try:
        result = subprocess.run(
            ["semgrep", "--config=auto", "--json", "--no-git-ignore", workspace_path],
            capture_output=True, text=True, timeout=300,
        )
        return json.loads(result.stdout) if result.stdout.strip() else {"results": []}
    except Exception as e:
        print(f"[Semgrep] Native fallback failed: {e}")
        return {"results": []}
