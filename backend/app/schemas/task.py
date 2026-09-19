"""Pydantic Request and Response Schemas for Tasks API."""
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.enums import NetworkPolicy, TaskState


class TaskCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="Natural language programming or analysis task")
    max_retries: int = Field(default=3, ge=1, le=10, description="Max repair attempts")
    network_policy: NetworkPolicy = Field(default=NetworkPolicy.DISABLED, description="Network egress policy")
    initial_files: List[str] = Field(default_factory=list, description="List of pre-uploaded workspace files")


class CodeVersionSummary(BaseModel):
    version: int
    version_tag: str
    entrypoint: str
    agent: str
    modification_reason: Optional[str] = None
    diff_from_parent: Optional[str] = None
    created_at: str


class ArtifactSummary(BaseModel):
    filename: str
    file_type: str
    file_size_bytes: int
    storage_path: str
    sha256_hash: Optional[str] = None


class TaskResponse(BaseModel):
    task_id: str
    prompt: str
    state: TaskState
    current_attempt: int
    max_retries: int
    created_at: str
    completed_at: Optional[str] = None
    total_duration_sec: float = 0.0
    final_status: Optional[str] = None
    error_message: Optional[str] = None
    plan: Optional[Dict[str, Any]] = None
    artifacts: List[ArtifactSummary] = Field(default_factory=list)
    code_versions: List[CodeVersionSummary] = Field(default_factory=list)
    latest_code: Optional[str] = None
    validation_passed: bool = False
    validation_score: Optional[float] = None
