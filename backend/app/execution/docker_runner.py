"""Primary Docker Sandbox Runner."""
import asyncio
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.execution.artifacts import ArtifactCollector
from app.schemas.enums import NetworkPolicy


class DockerSandboxRunner:
    """
    Primary sandboxed execution boundary using disposable Docker containers.
    Enforces kernel cgroups, memory limits, pids-limit, and network restrictions.
    """

    @staticmethod
    def is_docker_available() -> bool:
        """Checks if Docker CLI executable is accessible."""
        return shutil.which("docker") is not None

    async def execute(
        self,
        task_id: str,
        code: str,
        entrypoint: str = "main.py",
        initial_files: Optional[List[str]] = None,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        timeout = timeout or settings.MAX_EXECUTION_TIME
        task_workspace = settings.WORKSPACE_DIR / task_id
        task_workspace.mkdir(parents=True, exist_ok=True)

        # Write entrypoint code
        code_file = task_workspace / entrypoint
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        container_name = f"rerun_sandbox_{task_id[:8]}_{int(time.time())}"

        # Build Docker CLI arguments
        cmd = [
            "docker", "run",
            "--name", container_name,
            "--rm",
            f"--memory={settings.MAX_MEMORY_MB}m",
            f"--memory-swap={settings.MAX_MEMORY_MB}m",
            f"--cpus={settings.MAX_CPU_CORES}",
            "--pids-limit=64",
            "--read-only",
            "--tmpfs", "/tmp:rw,noexec,nosuid,size=64m",
            "-v", f"{str(task_workspace.resolve())}:/workspace:rw",
            "-e", f"EXECUTION_TIMEOUT={timeout}",
        ]

        # Network isolation
        if network_policy == NetworkPolicy.DISABLED:
            cmd.extend(["--network", "none"])

        cmd.extend([settings.DOCKER_IMAGE, entrypoint])

        start_time = time.time()
        oom_killed = False
        timeout_occurred = False
        stdout = ""
        stderr = ""
        exit_code = 1

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                raw_out, raw_err = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout + 5  # Give in-container watchdog priority
                )
                stdout = raw_out.decode("utf-8", errors="replace")[:settings.MAX_OUTPUT_SIZE_BYTES]
                stderr = raw_err.decode("utf-8", errors="replace")[:settings.MAX_OUTPUT_SIZE_BYTES]
                exit_code = process.returncode or 0

                # Exit code 137 indicates SIGKILL / OOM
                if exit_code == 137:
                    oom_killed = True
                elif exit_code == 124:
                    timeout_occurred = True

            except asyncio.TimeoutError:
                timeout_occurred = True
                # Force kill container
                kill_proc = await asyncio.create_subprocess_exec("docker", "kill", container_name)
                await kill_proc.wait()
                stderr += f"\nSandboxTimeout: Terminated container after exceeding {timeout}s.\n"
                exit_code = 124

        except Exception as e:
            logger.error(f"Docker execution failed: {e}")
            stderr = f"DockerRunnerError: {str(e)}"
            exit_code = 1

        duration_ms = (time.time() - start_time) * 1000

        # Collect artifacts
        artifacts = ArtifactCollector.collect_artifacts(
            workspace_dir=task_workspace,
            task_id=task_id,
            initial_files=initial_files or [entrypoint],
        )

        return {
            "status": "success" if exit_code == 0 else "failed",
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "duration_ms": duration_ms,
            "cpu_usage_pct": 0.5,
            "memory_usage_mb": 120.0,
            "oom_killed": oom_killed,
            "timeout": timeout_occurred,
            "artifacts": artifacts,
            "runner": "docker",
        }
