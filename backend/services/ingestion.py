"""
IngestionService
────────────────
Handles:
  • GitHub repo cloning via GitPython
  • ZIP file extraction
  • Language detection by file extension
"""
from __future__ import annotations

import io
import os
import shutil
import zipfile
from pathlib import Path
from typing import List

import git

from config import settings


LANGUAGE_EXTENSION_MAP: dict[str, list[str]] = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".mjs", ".cjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "ruby": [".rb"],
    "php": [".php"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
    "csharp": [".cs"],
    "rust": [".rs"],
    "yaml": [".yml", ".yaml"],
    "json": [".json"],
    "dockerfile": ["dockerfile"],
    "shell": [".sh", ".bash"],
}


class IngestionService:
    def __init__(self):
        self.workspace_base = Path(settings.workspace_dir)
        self.workspace_base.mkdir(parents=True, exist_ok=True)

    # ─── GitHub Clone ─────────────────────────────────────────────────────────
    def ingest_github(self, url: str, scan_id: str) -> Path:
        target = self.workspace_base / scan_id
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

        print(f"[Ingestion] Cloning {url} → {target}")
        git.Repo.clone_from(url, str(target), depth=1)
        return target

    # ─── ZIP Extraction ───────────────────────────────────────────────────────
    def ingest_zip(self, file_bytes: bytes, scan_id: str) -> Path:
        target = self.workspace_base / scan_id
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)

        print(f"[Ingestion] Extracting ZIP → {target}")
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            zf.extractall(str(target))
        return target

    # ─── Language Detection ───────────────────────────────────────────────────
    def detect_languages(self, workspace: Path) -> List[str]:
        found: set[str] = set()
        for file_path in workspace.rglob("*"):
            if not file_path.is_file():
                continue
            name_lower = file_path.name.lower()
            ext = file_path.suffix.lower()
            for lang, extensions in LANGUAGE_EXTENSION_MAP.items():
                if ext in extensions or name_lower in extensions:
                    found.add(lang)
        result = sorted(found)
        print(f"[Ingestion] Detected languages: {result}")
        return result

    # ─── Cleanup ──────────────────────────────────────────────────────────────
    def cleanup(self, scan_id: str):
        target = self.workspace_base / scan_id
        if target.exists():
            shutil.rmtree(target)
            print(f"[Ingestion] Cleaned up workspace: {target}")
