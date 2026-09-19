"""Baseline B: Simple Retry / Basic Reflection (Without Task-Level Semantic Validation)."""
from typing import Any, Dict
from app.agents.coding.agent import CodingAgent
from app.execution.engine import ExecutionEngine
from app.observation.observer import RuntimeObserver
from app.security.policy import SecurityPolicyEngine


class BaselineB:
    """
    Simple retry baseline.
    Assumes Exit Code 0 = Task Success without semantic validation (vulnerable to false successes).
    """

    def __init__(self, max_retries: int = 3):
        self.coder = CodingAgent()
        self.security = SecurityPolicyEngine()
        self.executor = ExecutionEngine()
        self.max_retries = max_retries

    async def run_task(self, task_id: str, prompt: str) -> Dict[str, Any]:
        current_prompt = prompt
        last_stderr = ""

        for attempt in range(1, self.max_retries + 1):
            if last_stderr:
                augmented_prompt = f"{current_prompt}\n\nPrevious attempt failed with error:\n{last_stderr}\nPlease fix the error."
            else:
                augmented_prompt = current_prompt

            code_payload = await self.coder.generate_code(task_prompt=augmented_prompt)

            sec_report = self.security.inspect_code(code_payload.code)
            if not sec_report.allowed:
                return {
                    "task_id": task_id,
                    "baseline": "Baseline_B_SimpleRetry",
                    "success": False,
                    "exit_code": 1,
                    "attempts": attempt,
                    "blocked": True,
                    "error": "; ".join(sec_report.violations),
                }

            raw_exec = await self.executor.execute_code(
                task_id=f"base_b_{task_id}",
                code=code_payload.code,
                entrypoint="main.py",
            )
            obs = RuntimeObserver.observe(raw_exec)

            # Baseline B treats exit_code == 0 as completion (fails to detect false success!)
            if obs.exit_code == 0:
                return {
                    "task_id": task_id,
                    "baseline": "Baseline_B_SimpleRetry",
                    "success": True,
                    "exit_code": 0,
                    "attempts": attempt,
                    "blocked": False,
                    "duration_ms": obs.duration_ms,
                    "artifacts_count": len(obs.artifacts),
                    "false_success_unverified": len(obs.artifacts) == 0 and "chart" in prompt.lower(),
                }

            last_stderr = obs.stderr or obs.error_message or "Execution failed"

        return {
            "task_id": task_id,
            "baseline": "Baseline_B_SimpleRetry",
            "success": False,
            "exit_code": 1,
            "attempts": self.max_retries,
            "blocked": False,
            "error": "Exceeded max retry limit.",
        }
