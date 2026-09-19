"""Pydantic Schemas for Recovery Agent."""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import ErrorType


class RecoveryDecision(BaseModel):
    diagnosis: str
    error_type: ErrorType
    repair_strategy: str
    modified_code: str
    dependencies: List[str] = Field(
        default_factory=lambda: ["pandas", "matplotlib"],
        description="Python packages required by the repaired code",
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    needs_replan: bool = False

    @field_validator("error_type", mode="before")
    @classmethod
    def normalize_error_type(cls, v):
        if isinstance(v, ErrorType):
            return v
        if isinstance(v, str):
            clean = v.strip().upper().replace(" ", "_").replace("-", "_")
            # Try direct enum match
            try:
                return ErrorType(clean)
            except ValueError:
                pass
            # Try fuzzy substring match
            for member in ErrorType:
                if member.value in clean or clean in member.value:
                    return member
        return ErrorType.UNKNOWN_ERROR

    @field_validator("modified_code", mode="before")
    @classmethod
    def clean_code_fences(cls, v):
        if not isinstance(v, str):
            return str(v)
        code_str = v.strip()
        if code_str.startswith("```"):
            lines = code_str.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            return "\n".join(lines).strip()
        return code_str

    @field_validator("confidence", mode="before")
    @classmethod
    def normalize_confidence(cls, v):
        try:
            val = float(v)
            if val > 1.0:
                val = val / 100.0
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return 1.0

    @field_validator("dependencies", mode="before")
    @classmethod
    def normalize_dependencies(cls, v):
        if isinstance(v, list):
            return [str(item) for item in v]
        elif isinstance(v, dict):
            deps = []
            for val in v.values():
                if isinstance(val, list):
                    deps.extend([str(i) for i in val])
                else:
                    deps.append(str(val))
            return deps
        elif isinstance(v, str):
            return [v]
        return ["pandas", "matplotlib"]
