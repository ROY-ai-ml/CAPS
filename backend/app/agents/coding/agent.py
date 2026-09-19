"""Coding Agent Implementation."""
from typing import Any, Dict, List, Optional

from app.agents.coding.schemas import GeneratedCodePayload
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider


class CodingAgent:
    """
    Generates standalone, modular, sandboxed Python code to fulfill planned subtasks.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def generate_code(
        self,
        task_prompt: str,
        plan: Optional[Dict[str, Any]] = None,
        available_files: Optional[List[str]] = None,
        context_notes: Optional[str] = None,
    ) -> GeneratedCodePayload:
        system_prompt = (
            "You are the Senior Software Engineer in the ReRun Autonomous Platform.\n"
            "Your job is to generate self-contained, robust Python 3.10 code to execute the specified task.\n"
            "Requirements:\n"
            "1. Output MUST be valid JSON with keys: 'language', 'code', 'dependencies', 'entrypoint', 'expected_outputs'.\n"
            "2. The code must be completely self-contained and run non-interactively.\n"
            "3. Any generated visualization must be saved as a file using plt.savefig() without calling plt.show().\n"
            "4. Never generate hostile shell calls, subprocesses, or host file deletions."
        )

        prompt_payload = {
            "task": task_prompt,
            "plan": plan or {},
            "workspace_files": available_files or [],
            "extra_context": context_notes or "",
        }

        resp = await self.llm.complete_structured(
            prompt=str(prompt_payload),
            system_prompt=system_prompt,
        )

        data = resp.structured or {}
        if "code" not in data:
            # Fallback extraction if raw string was returned
            data["code"] = resp.content
            data["language"] = "python"
            data["dependencies"] = ["pandas", "matplotlib"]
            data["entrypoint"] = "main.py"
            data["expected_outputs"] = ["sales_chart.png"]

        return GeneratedCodePayload.model_validate(data)
