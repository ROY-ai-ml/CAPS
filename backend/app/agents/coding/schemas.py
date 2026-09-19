"""Pydantic Schemas for Coding Agent."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class GeneratedCodePayload(BaseModel):
    language: str = "python"
    code: str
    dependencies: List[str] = Field(default_factory=list)
    entrypoint: str = "main.py"
    expected_outputs: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None

    @field_validator("code", mode="before")
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

    @field_validator("dependencies", "expected_outputs", mode="before")
    @classmethod
    def normalize_list(cls, v):
        if isinstance(v, list):
            res = []
            for item in v:
                if isinstance(item, dict):
                    res.append(str(item.get("name", str(item))))
                else:
                    res.append(str(item))
            return res
        elif isinstance(v, dict):
            res = []
            for val in v.values():
                if isinstance(val, list):
                    res.extend([str(i) for i in val])
                else:
                    res.append(str(val))
            return res
        elif isinstance(v, str):
            return [v]
        return []
