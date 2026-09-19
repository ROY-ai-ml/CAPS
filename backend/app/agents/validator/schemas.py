"""Pydantic Schemas for Task Validation."""
from typing import Any, Dict, List
from pydantic import BaseModel, Field


class ValidationCheck(BaseModel):
    name: str
    passed: bool
    detail: str


class TaskValidationResult(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    checks: List[ValidationCheck] = Field(default_factory=list)
    failures: List[str] = Field(default_factory=list)
    explanation: str
    is_false_success: bool = False
