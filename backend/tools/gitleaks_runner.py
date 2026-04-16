"""
Gitleaks Docker Runner
───────────────────────
Detects secrets, API keys, credentials, and tokens.

Two-pass strategy:
  1. Working tree scan  — catches secrets in current files
  2. Full git log scan  — walks ALL commits to find secrets ever committed
     (even if deleted/overwritten). This is the critical diff vs tools that
     only scan HEAD.

Returns a deduplicated list of leak findings (JSON array).
"""
from __future__ import annotations

import json
import subprocess
import os
from pathlib import Path

from config import settings


def _save_debug(workspace_path: str, tool: str, stdout: str, stderr: str, returncode: int):
    base = os.path.join(workspace_path, f"_debug_{tool}")
    with open(f"{base}_stdout.json", "w") as f:
        f.write(stdout or "(empty)")
    with open(f"{base}_stderr.txt", "w") as f:
        f.write(f"returncode: {returncode}\n\n{stderr or '(empty)'}")
    print(f"[{tool.upper()}] Debug files: {base}_stdout.json")


def _is_git_repo(workspace_path: str) -> bool:
    """Check whether the workspace contains a real git repository with at least one commit."""
    git_dir = Path(workspace_path) / ".git"
    if not git_dir.is_dir():
        return False
    try:
        result = subprocess.run(
            ["git", "-C", workspace_path, "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return False


def _run_gitleaks_pass(workspace_path: str, mode: str, extra_args: list) -> list:
    """Run one gitleaks native invocation. Returns parsed findings list."""
    cmd = [
        "gitleaks",
        "detect",
        f"--source={workspace_path}",
        "--report-format=json",
        "--report-path=/dev/stdout",
        "--exit-code=0",
        "--redact",
    ] + extra_args

    print(f"[Gitleaks] Running ({mode}): {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if not stdout or stdout == "null":
            return []

        data = json.loads(stdout)
        if not isinstance(data, list):
            return []

        for item in data:
            item["_scan_mode"] = mode
        return data

    except subprocess.TimeoutExpired:
        print(f"[Gitleaks] Timeout on {mode} — skipping pass")
        return []
    except json.JSONDecodeError as e:
        raise RuntimeError(f"[Gitleaks] JSON parse error ({mode}): {e}")
    except FileNotFoundError as e:
        raise RuntimeError(f"[Gitleaks] gitleaks command not found: {e}")


def _dedup_findings(findings: list) -> list:
    """Deduplicate findings across both scan passes using a composite key."""
    seen: dict[str, dict] = {}
    for f in findings:
        key = "|".join([
            str(f.get("RuleID", "")),
            str(f.get("File", "")),
            str(f.get("StartLine", "")),
            str(f.get("Match", ""))[:30],
        ])
        if key not in seen:
            seen[key] = f
        else:
            # Merge commit metadata: accumulate all commits where this secret appeared
            existing = seen[key]
            existing_commits = existing.get("_commits", [])
            if not existing_commits and existing.get("Commit"):
                existing_commits = [existing["Commit"]]
            new_commit = f.get("Commit", "")
            if new_commit and new_commit not in existing_commits:
                existing_commits.append(new_commit)
            existing["_commits"] = existing_commits
            # Prefer git_log entry (has richer commit metadata)
            if f.get("_scan_mode") == "git_log" and existing.get("_scan_mode") != "git_log":
                saved_commits = existing["_commits"]
                existing.update(f)
                existing["_commits"] = saved_commits

    return list(seen.values())


def run_gitleaks(workspace_path: str) -> list:
    """
    Execute Gitleaks via Docker with two-pass scanning:
      Pass 1: Working-tree (--no-git) — current files including untracked
      Pass 2: Full git history (--log-opts=--all) — every commit on every branch

    Returns a merged, deduplicated findings list.
    """
    all_findings: list = []

    # Pass 1: Working-tree scan
    tree_findings = _run_gitleaks_pass(
        workspace_path, mode="working_tree", extra_args=["--no-git"],
    )
    print(f"[Gitleaks] Working-tree pass: {len(tree_findings)} findings")
    all_findings.extend(tree_findings)

    # Pass 2: Full git history (only if valid git repo)
    if _is_git_repo(workspace_path):
        print("[Gitleaks] Git repo detected — running full commit history scan (all branches)")
        history_findings = _run_gitleaks_pass(
            workspace_path, mode="git_log", extra_args=["--log-opts=--all"],
        )
        print(f"[Gitleaks] History pass: {len(history_findings)} findings")
        all_findings.extend(history_findings)
    else:
        print("[Gitleaks] No git repo — skipping history scan")

    _save_debug(
        workspace_path, "gitleaks",
        json.dumps(all_findings, indent=2, default=str),
        f"passes: working_tree={len(tree_findings)}, history={len(all_findings) - len(tree_findings)}",
        0,
    )

    deduped = _dedup_findings(all_findings)
    print(f"[Gitleaks] Total after dedup: {len(deduped)} findings")
    return deduped
