"""
ESLint Docker Runner
─────────────────────
Runs ESLint on JavaScript/TypeScript files in the workspace.
Detects package.json for project-aware linting; falls back to recommended config.
Returns a list of ESLint message objects in JSON format.
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


def _has_eslint_config(workspace_path: str) -> bool:
    """Check if the project has an existing ESLint config."""
    workspace = Path(workspace_path)
    config_files = [
        ".eslintrc", ".eslintrc.js", ".eslintrc.cjs", ".eslintrc.yaml",
        ".eslintrc.yml", ".eslintrc.json", "eslint.config.js", "eslint.config.mjs",
    ]
    # Check root and one level deep
    for config in config_files:
        if (workspace / config).exists():
            return True
        for subdir in workspace.iterdir():
            if subdir.is_dir() and (subdir / config).exists():
                return True
    return False


def _has_package_json(workspace_path: str) -> bool:
    return (Path(workspace_path) / "package.json").exists()


def run_eslint(workspace_path: str) -> list:
    """Execute ESLint natively and return parsed JSON findings list."""

    has_config = _has_eslint_config(workspace_path)
    has_pkg = _has_package_json(workspace_path)

    # Default config injected when no project config exists
    # Covers: security, common errors, no-eval, prototype pollution, XSS patterns
    default_config = json.dumps({
        "parser": "@typescript-eslint/parser",
        "parserOptions": {
            "ecmaVersion": 2022,
            "sourceType": "module",
            "ecmaFeatures": {"jsx": True}
        },
        "plugins": ["@typescript-eslint", "security"],
        "extends": [
            "eslint:recommended",
            "plugin:security/recommended"
        ],
        "env": {"browser": True, "node": True, "es2022": True},
        "rules": {
            "no-eval": "error",
            "no-implied-eval": "error",
            "no-new-func": "error",
            "no-script-url": "error",
            "no-proto": "error",
            "no-extend-native": "error",
            "no-global-assign": "error",
            "no-unsafe-finally": "error",
            "no-alert": "warn",
            "security/detect-object-injection": "warn",
            "security/detect-non-literal-regexp": "warn",
            "security/detect-non-literal-fs-filename": "warn",
            "security/detect-child-process": "error",
            "security/detect-disable-mustache-escape": "error",
            "security/detect-eval-with-expression": "error",
            "security/detect-no-csrf-before-method-override": "error",
            "security/detect-possible-timing-attacks": "warn",
            "security/detect-pseudoRandomBytes": "warn",
            "security/detect-unsafe-regex": "warn",
        }
    })

    cmd = [
        "sh", "-c",
        "npm install --save-dev eslint@8 "
        "@typescript-eslint/parser@6 @typescript-eslint/eslint-plugin@6 "
        "eslint-plugin-security@1 eslint-plugin-react@7 "
        "--legacy-peer-deps --silent 2>/dev/null ; "
        "echo \"$DEFAULT_ESLINT_CONFIG\" > /tmp/.eslintrc.json ; "
        + (
            "npx eslint --format=json --no-eslintrc -c /tmp/.eslintrc.json "
            if not has_config
            else "npx eslint --format=json "
        )
        + "--ext .js,.jsx,.ts,.tsx,.mjs,.cjs "
        "--no-error-on-unmatched-pattern "
        "--max-warnings=-1 "
        "\"/src\" 2>/dev/null || true".replace("/src", workspace_path)
    ]

    print(f"[ESLint] Running (has_config={has_config}, has_package_json={has_pkg})")
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            cwd=workspace_path,
            env={**os.environ, "DEFAULT_ESLINT_CONFIG": default_config}
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        _save_debug(workspace_path, "eslint", stdout, stderr, result.returncode)

        print(f"[ESLint] returncode={result.returncode}")
        if stderr:
            print(f"[ESLint] stderr (first 500 chars):\n{stderr[:500]}")

        if not stdout:
            print("[ESLint] stdout was empty")
            return []

        # ESLint JSON output is an array of file results
        data = json.loads(stdout)
        if not isinstance(data, list):
            return []

        # Flatten: each file has a messages array
        all_messages = []
        for file_result in data:
            file_path = file_result.get("filePath", "unknown")
            # Make path absolute if it's relative
            if file_path.startswith(workspace_path):
                file_path = file_path[len(workspace_path):].lstrip("/")
            for msg in file_result.get("messages", []):
                msg["filePath"] = file_path
                all_messages.append(msg)

        count = len(all_messages)
        print(f"[ESLint] Found {count} messages across {len(data)} files")
        return all_messages

    except subprocess.TimeoutExpired:
        print("[ESLint] ⚠️  Timeout — skipping")
        return []
    except json.JSONDecodeError as e:
        print(f"[ESLint] ⚠️  JSON parse error: {e}")
        return []
    except FileNotFoundError as e:
        raise RuntimeError(f"[ESLint] npm/npx command not found: {e}")
    except Exception as e:
        raise RuntimeError(f"[ESLint] Native run failed: {e}")