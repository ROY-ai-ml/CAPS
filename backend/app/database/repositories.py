"""Data Access Layer and Repositories for ReRun."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AgentRunModel,
    ArtifactModel,
    CodeVersionModel,
    ErrorModel,
    ExecutionModel,
    RepairModel,
    SecurityEventModel,
    TaskEventModel,
    TaskModel,
    TaskPlanModel,
    ValidationModel,
)
from app.schemas.enums import TaskState


class TaskRepository:
    """Handles CRUD operations for Tasks and child entities."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_task(
        self,
        prompt: str,
        task_id: Optional[str] = None,
        max_retries: int = 3,
        network_policy: str = "DISABLED",
        config_json: Optional[Dict[str, Any]] = None,
    ) -> TaskModel:
        task = TaskModel(
            id=task_id,
            prompt=prompt,
            state=TaskState.RECEIVED.value,
            max_retries=max_retries,
            network_policy=network_policy,
            config_json=config_json or {},
        )
        self.session.add(task)
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def get_task(self, task_id: str) -> Optional[TaskModel]:
        stmt = select(TaskModel).where(TaskModel.id == task_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_latest_plan(self, task_id: str) -> Optional[TaskPlanModel]:
        stmt = select(TaskPlanModel).where(TaskPlanModel.task_id == task_id).order_by(TaskPlanModel.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def update_task_state(
        self,
        task_id: str,
        state: TaskState,
        attempt: Optional[int] = None,
        final_status: Optional[str] = None,
        error_message: Optional[str] = None,
    ):
        values: Dict[str, Any] = {"state": state.value}
        if attempt is not None:
            values["current_attempt"] = attempt
        if final_status is not None:
            values["final_status"] = final_status
            values["completed_at"] = datetime.now(timezone.utc)
        if error_message is not None:
            values["error_message"] = error_message

        stmt = update(TaskModel).where(TaskModel.id == task_id).values(**values)
        await self.session.execute(stmt)
        await self.session.commit()

    async def record_task_event(
        self,
        task_id: str,
        event_type: str,
        attempt: int = 1,
        agent_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> TaskEventModel:
        event = TaskEventModel(
            task_id=task_id,
            event_type=event_type,
            attempt=attempt,
            agent_name=agent_name,
            details_json=details or {},
        )
        self.session.add(event)
        await self.session.commit()
        return event

    async def record_plan(
        self,
        task_id: str,
        goal: str,
        subtasks: List[Any],
        dependencies: List[Any],
        expected_outputs: List[Any],
        validation_requirements: List[Any],
        constraints: List[Any],
        raw_plan: Optional[Dict[str, Any]] = None,
    ) -> TaskPlanModel:
        plan = TaskPlanModel(
            task_id=task_id,
            goal=goal,
            subtasks_json=subtasks,
            dependencies_json=dependencies,
            expected_outputs_json=expected_outputs,
            validation_requirements_json=validation_requirements,
            constraints_json=constraints,
            raw_plan_json=raw_plan,
        )
        self.session.add(plan)
        await self.session.commit()
        return plan

    async def record_code_version(
        self,
        task_id: str,
        version: int,
        version_tag: str,
        source_code: str,
        entrypoint: str = "main.py",
        dependencies: Optional[List[str]] = None,
        agent_name: str = "coding_agent",
        parent_version: Optional[int] = None,
        modification_reason: Optional[str] = None,
        diff_from_parent: Optional[str] = None,
    ) -> CodeVersionModel:
        cv = CodeVersionModel(
            task_id=task_id,
            version=version,
            version_tag=version_tag,
            source_code=source_code,
            entrypoint=entrypoint,
            dependencies_json=dependencies or [],
            agent_name=agent_name,
            parent_version=parent_version,
            modification_reason=modification_reason,
            diff_from_parent=diff_from_parent,
        )
        self.session.add(cv)
        await self.session.commit()
        return cv

    async def record_execution(
        self,
        task_id: str,
        code_version_id: Optional[str],
        attempt: int,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_ms: float,
        cpu_usage_pct: float,
        memory_usage_mb: float,
        oom_killed: bool = False,
        timeout: bool = False,
    ) -> ExecutionModel:
        exec_model = ExecutionModel(
            task_id=task_id,
            code_version_id=code_version_id,
            attempt=attempt,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            cpu_usage_pct=cpu_usage_pct,
            memory_usage_mb=memory_usage_mb,
            oom_killed=oom_killed,
            timeout=timeout,
        )
        self.session.add(exec_model)
        await self.session.commit()
        return exec_model

    async def record_error(
        self,
        task_id: str,
        execution_id: Optional[str],
        attempt: int,
        error_type: str,
        error_message: str,
        traceback_clean: str,
        failing_line: Optional[str] = None,
    ) -> ErrorModel:
        err = ErrorModel(
            task_id=task_id,
            execution_id=execution_id,
            attempt=attempt,
            error_type=error_type,
            error_message=error_message,
            traceback_clean=traceback_clean,
            failing_line=failing_line,
        )
        self.session.add(err)
        await self.session.commit()
        return err

    async def record_repair(
        self,
        task_id: str,
        error_id: Optional[str],
        attempt: int,
        diagnosis: str,
        repair_strategy: str,
        patch_summary: Optional[str] = None,
        confidence: float = 1.0,
        needs_replan: bool = False,
    ) -> RepairModel:
        repair = RepairModel(
            task_id=task_id,
            error_id=error_id,
            attempt=attempt,
            diagnosis=diagnosis,
            repair_strategy=repair_strategy,
            patch_summary=patch_summary,
            confidence=confidence,
            needs_replan=needs_replan,
        )
        self.session.add(repair)
        await self.session.commit()
        return repair

    async def record_validation(
        self,
        task_id: str,
        attempt: int,
        passed: bool,
        score: float,
        checks: List[Any],
        failures: List[str],
        explanation: str,
        is_false_success: bool = False,
    ) -> ValidationModel:
        val = ValidationModel(
            task_id=task_id,
            attempt=attempt,
            passed=passed,
            score=score,
            checks_json=checks,
            failures_json=failures,
            explanation=explanation,
            is_false_success=is_false_success,
        )
        self.session.add(val)
        await self.session.commit()
        return val

    async def record_artifact(
        self,
        task_id: str,
        filename: str,
        file_type: str,
        file_size_bytes: int,
        storage_path: str,
        sha256_hash: Optional[str] = None,
    ) -> ArtifactModel:
        art = ArtifactModel(
            task_id=task_id,
            filename=filename,
            file_type=file_type,
            file_size_bytes=file_size_bytes,
            storage_path=storage_path,
            sha256_hash=sha256_hash,
        )
        self.session.add(art)
        await self.session.commit()
        return art

    async def get_task_events(self, task_id: str) -> List[TaskEventModel]:
        stmt = select(TaskEventModel).where(TaskEventModel.task_id == task_id).order_by(TaskEventModel.timestamp.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_code_versions(self, task_id: str) -> List[CodeVersionModel]:
        stmt = select(CodeVersionModel).where(CodeVersionModel.task_id == task_id).order_by(CodeVersionModel.version.asc())
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def get_artifacts(self, task_id: str) -> List[ArtifactModel]:
        stmt = select(ArtifactModel).where(ArtifactModel.task_id == task_id)
        res = await self.session.execute(stmt)
        return list(res.scalars().all())
