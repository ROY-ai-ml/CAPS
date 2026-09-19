"""Runtime Observer Component."""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.observation.classifier import ErrorClassifier
from app.schemas.enums import ErrorType


@dataclass
class ObservationReport:
    """Structured synthesis of execution outputs for Master Agent evaluation."""
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    cpu_usage_pct: float
    memory_usage_mb: float
    artifacts: List[Dict[str, Any]]
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    failing_line: Optional[str] = None
    traceback_clean: Optional[str] = None
    oom_killed: bool = False
    timeout: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_ms": self.duration_ms,
            "artifacts_count": len(self.artifacts),
            "artifacts": self.artifacts,
            "error_type": self.error_type.value if self.error_type else None,
            "error_message": self.error_message,
            "failing_line": self.failing_line,
            "oom_killed": self.oom_killed,
            "timeout": self.timeout,
        }


class RuntimeObserver:
    """
    Transforms raw container stdout, stderr, and resource metrics into structured observations.
    """

    @classmethod
    def observe(cls, raw_exec_result: Dict[str, Any]) -> ObservationReport:
        exit_code = raw_exec_result.get("exit_code", 1)
        stdout = raw_exec_result.get("stdout", "")
        stderr = raw_exec_result.get("stderr", "")
        duration_ms = raw_exec_result.get("duration_ms", 0.0)
        cpu = raw_exec_result.get("cpu_usage_pct", 0.0)
        mem = raw_exec_result.get("memory_usage_mb", 0.0)
        artifacts = raw_exec_result.get("artifacts", [])
        oom = raw_exec_result.get("oom_killed", False)
        timeout = raw_exec_result.get("timeout", False)

        success = (exit_code == 0 and not oom and not timeout)

        error_type = None
        error_msg = None
        failing_line = None
        clean_traceback = None

        if not success:
            error_type, error_msg, failing_line = ErrorClassifier.classify(
                exit_code=exit_code,
                stderr=stderr,
                stdout=stdout,
                oom_killed=oom,
                timeout=timeout,
            )
            clean_traceback = stderr.strip()

        return ObservationReport(
            success=success,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            cpu_usage_pct=cpu,
            memory_usage_mb=mem,
            artifacts=artifacts,
            error_type=error_type,
            error_message=error_msg,
            failing_line=failing_line,
            traceback_clean=clean_traceback,
            oom_killed=oom,
            timeout=timeout,
        )
