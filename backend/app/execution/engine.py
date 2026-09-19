"""Execution Engine Orchestrator."""
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.execution.docker_runner import DockerSandboxRunner
from app.execution.fallback_runner import FallbackIsolatedRunner
from app.schemas.enums import NetworkPolicy


class ExecutionEngine:
    """
    Orchestrates sandboxed execution.
    Prefers Docker container isolation as the primary boundary.
    Employs the isolated process runner strictly as an offline testing fallback.
    """

    def __init__(self):
        self.docker_runner = DockerSandboxRunner()
        self.fallback_runner = FallbackIsolatedRunner()

    async def execute_code(
        self,
        task_id: str,
        code: str,
        entrypoint: str = "main.py",
        initial_files: Optional[List[str]] = None,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if self.docker_runner.is_docker_available():
            logger.info(f"Executing task {task_id} inside Primary Docker Sandbox")
            return await self.docker_runner.execute(
                task_id=task_id,
                code=code,
                entrypoint=entrypoint,
                initial_files=initial_files,
                network_policy=network_policy,
                timeout=timeout,
            )
        elif settings.ALLOW_LOCAL_FALLBACK_FOR_TESTING:
            logger.warning(
                f"Docker not found on host. Using Development Fallback Runner for task {task_id}. "
                "WARNING: Host isolation is weaker than containerization."
            )
            return await self.fallback_runner.execute(
                task_id=task_id,
                code=code,
                entrypoint=entrypoint,
                initial_files=initial_files,
                network_policy=network_policy,
                timeout=timeout,
            )
        else:
            raise RuntimeError(
                "Docker daemon is unavailable and local fallback is disabled in production. "
                "Execution halted safely to prevent untrusted execution on host."
            )
