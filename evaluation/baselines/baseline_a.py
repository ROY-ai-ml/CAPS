"""Baseline A: One-Shot LLM Code Generation (No Recovery)."""
from typing import Any, Dict
from app.agents.coding.agent import CodingAgent
from app.execution.engine import ExecutionEngine
from app.observation.observer import RuntimeObserver
from app.security.policy import SecurityPolicyEngine


class BaselineA:
    """One-shot direct generation and execution without recovery or validation."""

    def __init__(self):
        self.coder = CodingAgent()
        self.security = SecurityPolicyEngine()
        self.executor = ExecutionEngine()

    async def run_task(self, task_id: str, prompt: str) -> Dict[str, Any]:
        # 1. Generate code directly
        code_payload = await self.coder.generate_code(task_prompt=prompt)

        # 2. Check security
        sec_report = self.security.inspect_code(code_payload.code)
        if not sec_report.allowed:
            return {
                "task_id": task_id,
                "baseline": "Baseline_A_OneShot",
                "success": False,
                "exit_code": 1,
                "attempts": 1,
                "blocked": True,
                "error": "; ".join(sec_report.violations),
                "artifacts_count": 0,
            }

        # 3. Execute once
        raw_exec = await self.executor.execute_code(
            task_id=f"base_a_{task_id}",
            code=code_payload.code,
            entrypoint="main.py",
        )
        obs = RuntimeObserver.observe(raw_exec)

        return {
            "task_id": task_id,
            "baseline": "Baseline_A_OneShot",
            "success": obs.exit_code == 0,
            "exit_code": obs.exit_code,
            "attempts": 1,
            "blocked": False,
            "duration_ms": obs.duration_ms,
            "artifacts_count": len(obs.artifacts),
            "error": obs.error_message if obs.exit_code != 0 else None,
        }
