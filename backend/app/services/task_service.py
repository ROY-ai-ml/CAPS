"""Task Execution Service managing async workers and active orchestrators."""
import asyncio
import uuid
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.master.orchestrator import MasterAgentOrchestrator
from app.core.config import settings
from app.core.logging import logger
from app.database.models import TaskModel
from app.database.repositories import TaskRepository
from app.database.session import AsyncSessionLocal
from app.schemas.enums import NetworkPolicy, TaskState

# Concurrency limiter
task_semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TASKS)

# In-memory registry for active orchestrators (enabling human cancellation)
active_tasks: Dict[str, MasterAgentOrchestrator] = {}


class TaskService:
    """Orchestrates asynchronous background worker execution for tasks."""

    @staticmethod
    async def create_and_spawn_task(
        prompt: str,
        max_retries: int = 3,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        initial_files: Optional[list] = None,
    ) -> str:
        task_id = str(uuid.uuid4())

        async with AsyncSessionLocal() as session:
            repo = TaskRepository(session)
            await repo.create_task(
                task_id=task_id,
                prompt=prompt,
                max_retries=max_retries,
                network_policy=network_policy.value,
            )

        # Spawn asynchronous worker without blocking HTTP request
        asyncio.create_task(
            TaskService._run_worker(
                task_id=task_id,
                prompt=prompt,
                max_retries=max_retries,
                network_policy=network_policy,
                initial_files=initial_files or [],
            )
        )
        return task_id

    @staticmethod
    async def _run_worker(
        task_id: str,
        prompt: str,
        max_retries: int,
        network_policy: NetworkPolicy,
        initial_files: list,
    ):
        async with task_semaphore:
            async with AsyncSessionLocal() as session:
                orchestrator = MasterAgentOrchestrator(
                    task_id=task_id,
                    prompt=prompt,
                    db_session=session,
                    max_retries=max_retries,
                    network_policy=network_policy,
                    initial_files=initial_files,
                )
                active_tasks[task_id] = orchestrator

                try:
                    logger.info(f"Worker started for task {task_id}")
                    await orchestrator.run()
                    logger.info(f"Worker finished for task {task_id} with state: {orchestrator.context.current_state.value}")
                except Exception as e:
                    logger.error(f"Worker failed for task {task_id}: {e}", exc_info=True)
                finally:
                    if task_id in active_tasks:
                        del active_tasks[task_id]

    @staticmethod
    async def cancel_task(task_id: str) -> bool:
        """Cancels an ongoing task."""
        if task_id in active_tasks:
            orchestrator = active_tasks[task_id]
            await orchestrator.cancel(reason="User cancelled execution via API")
            return True

        # If not active in memory, update in DB
        async with AsyncSessionLocal() as session:
            repo = TaskRepository(session)
            task = await repo.get_task(task_id)
            if task and task.state not in [TaskState.COMPLETED.value, TaskState.FAILED.value, TaskState.CANCELLED.value]:
                await repo.update_task_state(task_id, TaskState.CANCELLED, final_status="cancelled")
                return True
        return False
