"""
Pylint Docker Runner
─────────────────────
Runs Pylint on Python files in the workspace.
Returns a list of message dicts in Pylint's JSON format.
"""
from __future__ import annotations

import json
import subprocess
from config import settings


def run_pylint(workspace_path: str) -> list:
    """Execute Pylint via Docker and return parsed JSON message list."""

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{workspace_path}:/src:ro",
        settings.pylint_image,
        "--output-format=json",
        "--recursive=y",
        "--disable=C0114,C0115,C0116",   # Skip missing-docstring warnings
        "/src",
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
        if not stdout:
            print("[Pylint] No output")
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
        print("[Pylint] ⚠️  Docker not found — trying native pylint")
        return _run_pylint_native(workspace_path)


def _run_pylint_native(workspace_path: str) -> list:
    """Fallback: run pylint natively."""
    try:
        result = subprocess.run(
            ["pylint", "--output-format=json", "--recursive=y", workspace_path],
            capture_output=True, text=True, timeout=180,
        )
        stdout = result.stdout.strip()
        return json.loads(stdout) if stdout else []
    except Exception as e:
        print(f"[Pylint] Native fallback failed: {e}")
        return []
