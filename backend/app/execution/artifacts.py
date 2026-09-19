"""Artifacts Management and Collection."""
import hashlib
import mimetypes
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

from app.core.config import settings


def compute_sha256(filepath: Path) -> str:
    """Calculates SHA256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ArtifactCollector:
    """Discovers, catalogs, and archives output artifacts created by executions."""

    @staticmethod
    def collect_artifacts(
        workspace_dir: Path,
        task_id: str,
        initial_files: List[str],
    ) -> List[Dict[str, Any]]:
        artifacts = []
        task_store_dir = settings.ARTIFACTS_DIR / task_id
        task_store_dir.mkdir(parents=True, exist_ok=True)

        for item in workspace_dir.iterdir():
            if item.is_file() and item.name not in initial_files and not item.name.endswith(".pyc"):
                size = item.stat().st_size
                if size > settings.MAX_FILE_SIZE_BYTES:
                    continue

                mime_type, _ = mimetypes.guess_type(item.name)
                mime_type = mime_type or "application/octet-stream"

                # Archive into central store
                target_path = task_store_dir / item.name
                shutil.copy2(item, target_path)

                checksum = compute_sha256(target_path)

                artifacts.append({
                    "filename": item.name,
                    "file_type": mime_type,
                    "file_size_bytes": size,
                    "storage_path": str(target_path),
                    "sha256_hash": checksum,
                })

        return artifacts
