"""SQLAlchemy Relational Database Models for ReRun."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship

from app.database.session import Base
from app.schemas.enums import ErrorType, FinalStatus, NetworkPolicy, TaskState


def get_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TaskModel(Base):
    """Core Task Entity tracking the entire autonomous lifecycle."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=get_uuid)
    prompt = Column(Text, nullable=False)
    state = Column(String(32), default=TaskState.RECEIVED.value, index=True)
    current_attempt = Column(Integer, default=1)
    max_retries = Column(Integer, default=3)
    network_policy = Column(String(16), default=NetworkPolicy.DISABLED.value)
    
    final_status = Column(String(32), nullable=True)
    error_message = Column(Text, nullable=True)
    total_duration_sec = Column(Float, default=0.0)
    config_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=get_utc_now)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    plans = relationship("TaskPlanModel", back_populates="task", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRunModel", back_populates="task", cascade="all, delete-orphan")
    code_versions = relationship("CodeVersionModel", back_populates="task", cascade="all, delete-orphan")
    executions = relationship("ExecutionModel", back_populates="task", cascade="all, delete-orphan")
    errors = relationship("ErrorModel", back_populates="task", cascade="all, delete-orphan")
    repairs = relationship("RepairModel", back_populates="task", cascade="all, delete-orphan")
    validations = relationship("ValidationModel", back_populates="task", cascade="all, delete-orphan")
    artifacts = relationship("ArtifactModel", back_populates="task", cascade="all, delete-orphan")
    security_events = relationship("SecurityEventModel", back_populates="task", cascade="all, delete-orphan")
    events = relationship("TaskEventModel", back_populates="task", cascade="all, delete-orphan")
    resource_metrics = relationship("ResourceMetricModel", back_populates="task", cascade="all, delete-orphan")


class TaskPlanModel(Base):
    """Structured plan produced by the Planner Agent."""
    __tablename__ = "task_plans"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    goal = Column(Text, nullable=False)
    subtasks_json = Column(JSON, default=list)
    dependencies_json = Column(JSON, default=list)
    expected_outputs_json = Column(JSON, default=list)
    validation_requirements_json = Column(JSON, default=list)
    constraints_json = Column(JSON, default=list)
    raw_plan_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="plans")


class AgentModel(Base):
    """Registered Specialized Agent definitions."""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=get_uuid)
    name = Column(String(64), unique=True, nullable=False)
    role = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)


class AgentRunModel(Base):
    """Audit record for every agent invocation."""
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    agent_name = Column(String(64), nullable=False)
    attempt = Column(Integer, default=1)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    status = Column(String(32), default="success")
    duration_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="agent_runs")


class CodeVersionModel(Base):
    """Immutable record of each generated or repaired program."""
    __tablename__ = "code_versions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    version_tag = Column(String(32), nullable=False)  # attempt_1, attempt_2
    source_code = Column(Text, nullable=False)
    entrypoint = Column(String(64), default="main.py")
    dependencies_json = Column(JSON, default=list)
    agent_name = Column(String(64), default="coding_agent")
    parent_version = Column(Integer, nullable=True)
    modification_reason = Column(Text, nullable=True)
    diff_from_parent = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="code_versions")
    executions = relationship("ExecutionModel", back_populates="code_version")


class ExecutionModel(Base):
    """Sandbox execution telemetry and outputs."""
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    code_version_id = Column(String(36), ForeignKey("code_versions.id"), nullable=True)
    attempt = Column(Integer, nullable=False)
    exit_code = Column(Integer, nullable=False)
    stdout = Column(Text, default="")
    stderr = Column(Text, default="")
    duration_ms = Column(Float, default=0.0)
    cpu_usage_pct = Column(Float, default=0.0)
    memory_usage_mb = Column(Float, default=0.0)
    oom_killed = Column(Boolean, default=False)
    timeout = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="executions")
    code_version = relationship("CodeVersionModel", back_populates="executions")
    errors = relationship("ErrorModel", back_populates="execution")
    resource_metrics = relationship("ResourceMetricModel", back_populates="execution")


class ErrorModel(Base):
    """Diagnosed error record associated with an execution."""
    __tablename__ = "errors"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=True)
    attempt = Column(Integer, nullable=False)
    error_type = Column(String(32), default=ErrorType.UNKNOWN_ERROR.value)
    error_message = Column(Text, nullable=False)
    traceback_clean = Column(Text, nullable=True)
    failing_line = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="errors")
    execution = relationship("ExecutionModel", back_populates="errors")
    repairs = relationship("RepairModel", back_populates="error")


class RepairModel(Base):
    """Recovery strategy and diagnosis by Recovery Agent."""
    __tablename__ = "repairs"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    error_id = Column(String(36), ForeignKey("errors.id"), nullable=True)
    attempt = Column(Integer, nullable=False)
    diagnosis = Column(Text, nullable=False)
    repair_strategy = Column(Text, nullable=False)
    patch_summary = Column(Text, nullable=True)
    confidence = Column(Float, default=1.0)
    needs_replan = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="repairs")
    error = relationship("ErrorModel", back_populates="repairs")


class ValidationModel(Base):
    """Task-level verification result."""
    __tablename__ = "validations"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    attempt = Column(Integer, nullable=False)
    passed = Column(Boolean, nullable=False)
    score = Column(Float, default=0.0)
    checks_json = Column(JSON, default=list)
    failures_json = Column(JSON, default=list)
    explanation = Column(Text, nullable=False)
    is_false_success = Column(Boolean, default=False)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="validations")


class ArtifactModel(Base):
    """Captured output artifact (chart, CSV, PDF, JSON)."""
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), default="binary")
    file_size_bytes = Column(Integer, default=0)
    storage_path = Column(Text, nullable=False)
    sha256_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="artifacts")


class SecurityEventModel(Base):
    """Audit log for policy checks and security rejections."""
    __tablename__ = "security_events"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    code_version_id = Column(String(36), nullable=True)
    attempt = Column(Integer, default=1)
    allowed = Column(Boolean, nullable=False)
    risk_level = Column(String(16), default="low")
    violations_json = Column(JSON, default=list)
    warnings_json = Column(JSON, default=list)
    created_at = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="security_events")


class ResourceMetricModel(Base):
    """Fine-grained resource utilization metrics."""
    __tablename__ = "resource_metrics"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    execution_id = Column(String(36), ForeignKey("executions.id"), nullable=True)
    cpu_percent = Column(Float, default=0.0)
    memory_rss_bytes = Column(Integer, default=0)
    duration_sec = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="resource_metrics")
    execution = relationship("ExecutionModel", back_populates="resource_metrics")


class TaskEventModel(Base):
    """Fine-grained chronological event stream for debugging and live trace."""
    __tablename__ = "task_events"

    id = Column(String(36), primary_key=True, default=get_uuid)
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    attempt = Column(Integer, default=1)
    agent_name = Column(String(64), nullable=True)
    details_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=get_utc_now)

    task = relationship("TaskModel", back_populates="events")
