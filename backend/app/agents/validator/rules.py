"""Deterministic Semantic Rules for Task Validation."""
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple


class SemanticValidationRules:
    """Deterministic checks for artifacts and data science outputs."""

    @staticmethod
    def check_file_deliverables(
        expected_outputs: List[Dict[str, Any]],
        actual_artifacts: List[Dict[str, Any]],
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        checks = []
        failures = []

        artifact_names = {a["filename"]: a for a in actual_artifacts}

        for exp in expected_outputs:
            if hasattr(exp, "name"):
                exp_name = exp.name
                is_req = getattr(exp, "required", True)
            elif isinstance(exp, dict):
                exp_name = exp.get("name", "")
                is_req = exp.get("required", True)
            else:
                exp_name = str(exp)
                is_req = True

            if exp_name in artifact_names:
                art = artifact_names[exp_name]
                size = art.get("file_size_bytes", 0)

                # Check minimum plausible size (e.g. valid PNG > 500 bytes)
                if size < 200:
                    failures.append(f"Deliverable '{exp_name}' was generated but is abnormally small ({size} bytes).")
                    checks.append({
                        "name": f"deliverable_size_{exp_name}",
                        "passed": False,
                        "detail": f"File size {size} bytes is below threshold.",
                    })
                else:
                    checks.append({
                        "name": f"deliverable_exists_{exp_name}",
                        "passed": True,
                        "detail": f"Artifact '{exp_name}' created successfully ({size} bytes).",
                    })
            elif is_req:
                failures.append(f"Required deliverable '{exp_name}' was not produced by the program.")
                checks.append({
                    "name": f"deliverable_exists_{exp_name}",
                    "passed": False,
                    "detail": f"Missing expected file '{exp_name}'.",
                })

        return checks, failures

    @staticmethod
    def check_stdout_calculations(stdout: str, task_prompt: str) -> Tuple[List[Dict[str, Any]], List[str]]:
        checks = []
        failures = []

        prompt_lower = task_prompt.lower()

        # If user asked for monthly revenue / sales calculation
        if "monthly" in prompt_lower or "revenue" in prompt_lower or "calculate" in prompt_lower:
            has_numbers = any(char.isdigit() for char in stdout)
            if not has_numbers and "sales" in prompt_lower:
                failures.append("Execution stdout does not show numerical results for requested calculations.")
                checks.append({
                    "name": "calculation_output_present",
                    "passed": False,
                    "detail": "No numerical aggregate values detected in runtime stdout.",
                })
            else:
                checks.append({
                    "name": "calculation_output_present",
                    "passed": True,
                    "detail": "Numerical aggregate values detected in stdout.",
                })

        return checks, failures
