"""Planner Agent Implementation."""
from typing import Any, Dict, List, Optional

from app.agents.planner.schemas import PlanOutput
from app.llm.base import BaseLLMProvider
from app.llm.factory import get_llm_provider


class PlannerAgent:
    """
    Decomposes natural language user goals into structured, actionable subtask plans.
    """

    def __init__(self, llm_provider: Optional[BaseLLMProvider] = None):
        self.llm = llm_provider or get_llm_provider()

    async def plan(
        self,
        task_prompt: str,
        available_files: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
    ) -> PlanOutput:
        system_prompt = (
            "You are the Lead Technical Planner in the ReRun Autonomous Architecture.\n"
            "Your objective is to decompose the user's task into a rigorous, structured execution plan.\n"
            "You must return ONLY valid JSON with keys: 'goal', 'requirements', 'subtasks', "
            "'dependencies', 'expected_outputs', 'validation_requirements', 'constraints'.\n"
            "Subtasks must have: 'id', 'name', 'dependencies'."
        )

        files_str = ", ".join(available_files) if available_files else "None provided"
        constraints_str = ", ".join(constraints) if constraints else "Default sandbox constraints apply"

        user_content = (
            f"User Objective: {task_prompt}\n"
            f"Available Files in Workspace: {files_str}\n"
            f"Active Constraints: {constraints_str}\n\n"
            "Synthesize an execution plan with explicit validation requirements."
        )

        resp = await self.llm.complete_structured(
            prompt=user_content,
            system_prompt=system_prompt,
        )

        data = resp.structured or {}
        # Fallback if keys missing
        if "goal" not in data:
            data["goal"] = task_prompt
        if "subtasks" not in data:
            data["subtasks"] = [
                {"id": 1, "name": "Load and preprocess data", "dependencies": []},
                {"id": 2, "name": "Execute analytical logic", "dependencies": [1]},
                {"id": 3, "name": "Render and save artifacts", "dependencies": [2]}
            ]
        if "expected_outputs" not in data:
            data["expected_outputs"] = [{"name": "output.png", "type": "image", "required": False}]

        return PlanOutput.model_validate(data)
