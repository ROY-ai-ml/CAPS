"""Pydantic Schemas for Planner Agent."""
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class Subtask(BaseModel):
    id: Union[int, str]
    name: str
    description: Optional[str] = None
    dependencies: List[Union[int, str]] = Field(default_factory=list)


class ExpectedOutput(BaseModel):
    name: str
    type: str = "file"  # "image", "csv", "json", "text", "file"
    required: bool = True


class PlanOutput(BaseModel):
    goal: str
    requirements: List[str] = Field(default_factory=list)
    subtasks: List[Subtask] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    expected_outputs: List[ExpectedOutput] = Field(default_factory=list)
    validation_requirements: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)

    @field_validator("dependencies", mode="before")
    @classmethod
    def normalize_dependencies(cls, v):
        if isinstance(v, list):
            return [str(item) for item in v]
        elif isinstance(v, dict):
            deps = []
            for val in v.values():
                if isinstance(val, list):
                    deps.extend([str(item) for item in val])
                elif isinstance(val, str):
                    deps.append(val)
            return deps
        elif isinstance(v, str):
            return [v]
        return []

    @field_validator("requirements", "validation_requirements", "constraints", mode="before")
    @classmethod
    def normalize_string_lists(cls, v):
        if isinstance(v, list):
            return [str(item) for item in v]
        elif isinstance(v, dict):
            items = []
            for val in v.values():
                if isinstance(val, list):
                    items.extend([str(i) for i in val])
                elif isinstance(val, str):
                    items.append(val)
            return items
        elif isinstance(v, str):
            return [v]
        return []

    @field_validator("expected_outputs", mode="before")
    @classmethod
    def normalize_expected_outputs(cls, v):
        if not isinstance(v, list):
            return []
        normalized = []
        for item in v:
            if isinstance(item, str):
                normalized.append(ExpectedOutput(name=item, type="file", required=True))
            elif isinstance(item, dict):
                normalized.append(ExpectedOutput(**item))
            elif isinstance(item, ExpectedOutput):
                normalized.append(item)
        return normalized

