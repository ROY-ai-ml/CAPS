"""FastAPI Routes for Task Lifecycle Management."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.models import CodeVersionModel, TaskEventModel, TaskModel, ValidationModel
from app.database.repositories import TaskRepository
from app.database.session import get_db_session
from app.schemas.enums import TaskState
from app.schemas.task import ArtifactSummary, CodeVersionSummary, TaskCreateRequest, TaskResponse
from app.services.task_service import TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_task(req: TaskCreateRequest):
    """Submits a new task for asynchronous autonomous execution."""
    task_id = await TaskService.create_and_spawn_task(
        prompt=req.prompt,
        max_retries=req.max_retries,
        network_policy=req.network_policy,
        initial_files=req.initial_files,
    )
    return {
        "task_id": task_id,
        "status": "accepted",
        "state": TaskState.RECEIVED.value,
        "message": "Task received and queued for autonomous planning and execution."
    }


@router.get("", response_model=Dict[str, Any])
async def list_tasks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    """Lists recent tasks with high-level statistics."""
    stmt = select(TaskModel).order_by(desc(TaskModel.created_at)).offset(offset).limit(limit)
    res = await db.execute(stmt)
    tasks = res.scalars().all()

    # Aggregate platform statistics
    total_q = select(func.count(TaskModel.id))
    completed_q = select(func.count(TaskModel.id)).where(TaskModel.state == TaskState.COMPLETED.value)
    failed_q = select(func.count(TaskModel.id)).where(TaskModel.state == TaskState.FAILED.value)

    total_count = (await db.execute(total_q)).scalar() or 0
    completed_count = (await db.execute(completed_q)).scalar() or 0
    failed_count = (await db.execute(failed_q)).scalar() or 0

    return {
        "tasks": [
            {
                "id": t.id,
                "prompt": t.prompt,
                "state": t.state,
                "current_attempt": t.current_attempt,
                "max_retries": t.max_retries,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "duration_sec": t.total_duration_sec,
                "final_status": t.final_status,
            }
            for t in tasks
        ],
        "stats": {
            "total_tasks": total_count,
            "completed_tasks": completed_count,
            "failed_tasks": failed_count,
            "success_rate": round(completed_count / total_count, 2) if total_count > 0 else 0.0,
        }
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieves comprehensive task state, code versions, artifacts, and plan."""
    repo = TaskRepository(db)
    task = await repo.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found.")

    # Fetch related items
    code_vers = await repo.get_code_versions(task_id)
    artifacts = await repo.get_artifacts(task_id)
    latest_plan = await repo.get_latest_plan(task_id)

    # Fetch latest validation
    val_stmt = select(ValidationModel).where(ValidationModel.task_id == task_id).order_by(desc(ValidationModel.attempt))
    latest_val = (await db.execute(val_stmt)).scalars().first()

    return TaskResponse(
        task_id=task.id,
        prompt=task.prompt,
        state=TaskState(task.state),
        current_attempt=task.current_attempt,
        max_retries=task.max_retries,
        created_at=task.created_at.isoformat() if task.created_at else "",
        completed_at=task.completed_at.isoformat() if task.completed_at else None,
        total_duration_sec=task.total_duration_sec or 0.0,
        final_status=task.final_status,
        error_message=task.error_message,
        plan=latest_plan.raw_plan_json if latest_plan else None,
        artifacts=[
            ArtifactSummary(
                filename=a.filename,
                file_type=a.file_type,
                file_size_bytes=a.file_size_bytes,
                storage_path=a.storage_path,
                sha256_hash=a.sha256_hash,
            )
            for a in artifacts
        ],
        code_versions=[
            CodeVersionSummary(
                version=cv.version,
                version_tag=cv.version_tag,
                entrypoint=cv.entrypoint,
                agent=cv.agent_name,
                modification_reason=cv.modification_reason,
                diff_from_parent=cv.diff_from_parent,
                created_at=cv.created_at.isoformat() if cv.created_at else "",
            )
            for cv in code_vers
        ],
        latest_code=code_vers[-1].source_code if code_vers else None,
        validation_passed=latest_val.passed if latest_val else False,
        validation_score=latest_val.score if latest_val else None,
    )


@router.post("/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Human override: cancels an active task execution."""
    success = await TaskService.cancel_task(task_id)
    if not success:
        raise HTTPException(status_code=400, detail="Task is already terminal or does not exist.")
    return {"task_id": task_id, "status": "cancelled", "message": "Task cancellation signal sent."}


@router.get("/{task_id}/events")
async def get_task_events(task_id: str, db: AsyncSession = Depends(get_db_session)):
    """Retrieves full chronological audit trail of events for a task."""
    repo = TaskRepository(db)
    events = await repo.get_task_events(task_id)
    return [
        {
            "id": e.id,
            "event_type": e.event_type,
            "attempt": e.attempt,
            "agent_name": e.agent_name,
            "details": e.details_json,
            "timestamp": e.timestamp.isoformat() if e.timestamp else "",
        }
        for e in events
    ]


@router.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Uploads a dataset or input file into the shared uploads repository."""
    upload_dir = settings.WORKSPACE_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / file.filename

    with open(target_path, "wb") as f:
        content = await file.read()
        f.write(content)

    return {
        "filename": file.filename,
        "size_bytes": len(content),
        "path": str(target_path),
        "message": "File successfully uploaded."
    }
