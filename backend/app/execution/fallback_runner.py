"""Development & Offline Testing Fallback Process Runner."""
import asyncio
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from app.core.config import settings
from app.core.logging import logger
from app.execution.artifacts import ArtifactCollector
from app.schemas.enums import NetworkPolicy


class FallbackIsolatedRunner:
    """
    Development and offline testing fallback runner.
    CAUTION: Host process isolation is fundamentally weaker than Docker containerization.
    This runner is strictly enabled for offline testing and CI environments.
    """

    async def execute(
        self,
        task_id: str,
        code: str,
        entrypoint: str = "main.py",
        initial_files: Optional[List[str]] = None,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        timeout: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not settings.ALLOW_LOCAL_FALLBACK_FOR_TESTING:
            raise RuntimeError(
                "Local fallback runner is disabled in production. Untrusted code must execute inside Docker."
            )

        timeout = timeout or settings.MAX_EXECUTION_TIME
        task_workspace = settings.WORKSPACE_DIR / task_id
        task_workspace.mkdir(parents=True, exist_ok=True)

        # Write entrypoint in workspace
        code_file = task_workspace / entrypoint
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        # Build clean environment with all secrets and API keys scrubbed
        clean_env = {}
        for k, v in os.environ.items():
            k_upper = k.upper()
            if any(secret_word in k_upper for secret_word in ["KEY", "TOKEN", "SECRET", "AUTH", "PASS", "CREDENTIAL"]):
                continue
            clean_env[k] = v

        clean_env["PYTHONUNBUFFERED"] = "1"
        clean_env["MPLBACKEND"] = "Agg"  # Headless matplotlib

        start_time = time.time()
        timeout_occurred = False
        oom_killed = False
        stdout = ""
        stderr = ""
        exit_code = 1
        peak_cpu = 0.0
        peak_rss_mb = 0.0

        # Execute using current python interpreter (.venv/Scripts/python)
        python_bin = sys.executable

        try:
            process = await asyncio.create_subprocess_exec(
                python_bin,
                entrypoint,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(task_workspace.resolve()),
                env=clean_env,
            )

            # Async monitoring task that samples CPU/memory via psutil
            async def _monitor_process(pid: int):
                nonlocal peak_cpu, peak_rss_mb
                try:
                    proc = psutil.Process(pid)
                    while True:
                        try:
                            cpu = proc.cpu_percent(interval=None)
                            mem_mb = proc.memory_info().rss / (1024 * 1024)
                            if cpu > peak_cpu:
                                peak_cpu = cpu
                            if mem_mb > peak_rss_mb:
                                peak_rss_mb = mem_mb
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            break
                        await asyncio.sleep(0.5)
                except Exception:
                    pass

            monitor_task = asyncio.create_task(_monitor_process(process.pid))

            try:
                raw_out, raw_err = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout,
                )
                stdout = raw_out.decode("utf-8", errors="replace")[:settings.MAX_OUTPUT_SIZE_BYTES]
                stderr = raw_err.decode("utf-8", errors="replace")[:settings.MAX_OUTPUT_SIZE_BYTES]
                exit_code = process.returncode or 0

            except asyncio.TimeoutError:
                timeout_occurred = True
                try:
                    process.kill()
                    await asyncio.wait_for(process.wait(), timeout=2.0)
                except Exception:
                    pass
                stderr += f"\nSandboxTimeout: Execution terminated after exceeding {timeout}s limit.\n"
                exit_code = 124
            finally:
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass

        except Exception as e:
            logger.error(f"Fallback execution error: {e}")
            stderr = f"FallbackRunnerError: {str(e)}"
            exit_code = 1

        duration_ms = (time.time() - start_time) * 1000

        # Collect generated artifacts
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
            "cpu_usage_pct": round(peak_cpu, 2),
            "memory_usage_mb": round(peak_rss_mb, 2),
            "oom_killed": oom_killed,
            "timeout": timeout_occurred,
            "artifacts": artifacts,
            "runner": "local_isolated_fallback",
        }
