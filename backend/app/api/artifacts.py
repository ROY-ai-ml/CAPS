"""Artifacts Inspection and Download API."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.repositories import TaskRepository
from app.database.session import get_db_session

router = APIRouter(prefix="/artifacts", tags=["Artifacts"])


@router.get("/{task_id}/{filename}")
async def download_artifact(
    task_id: str,
    filename: str,
    db: AsyncSession = Depends(get_db_session),
):
    """Securely serves generated artifacts without exposing arbitrary host filesystem."""
    repo = TaskRepository(db)
    artifacts = await repo.get_artifacts(task_id)

    target_artifact = next((a for a in artifacts if a.filename == filename), None)
    if not target_artifact:
        # Fallback check directly in artifacts store
        expected_path = settings.ARTIFACTS_DIR / task_id / filename
        if not expected_path.exists():
            raise HTTPException(status_code=404, detail=f"Artifact '{filename}' not found for task '{task_id}'.")
        filepath = expected_path
    else:
        filepath = Path(target_artifact.storage_path)

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Artifact file missing from storage.")

    # Guard against path traversal
    try:
        resolved = filepath.resolve()
        artifacts_root = settings.ARTIFACTS_DIR.resolve()
        if not str(resolved).startswith(str(artifacts_root)):
            raise HTTPException(status_code=403, detail="Access denied.")
    except Exception:
        raise HTTPException(status_code=403, detail="Invalid path.")

    return FileResponse(
        path=str(filepath),
        filename=filename,
        media_type=target_artifact.file_type if target_artifact else "application/octet-stream",
    )
