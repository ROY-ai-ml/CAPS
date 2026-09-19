"""Unit Tests for TaskValidationAgent."""
import pytest
from app.agents.master.context import ExecutionRecord, TaskContext
from app.agents.validator.agent import TaskValidationAgent


@pytest.mark.asyncio
async def test_validation_passes_with_artifact_and_calculations():
    context = TaskContext(
        task_id="test-1",
        prompt="Analyze sales.csv and generate sales_chart.png",
        plan={"expected_outputs": [{"name": "sales_chart.png", "type": "image", "required": True}]},
    )
    context.artifacts = [
        {"filename": "sales_chart.png", "file_type": "image/png", "file_size_bytes": 15000}
    ]
    context.record_execution(ExecutionRecord(
        attempt=1,
        exit_code=0,
        stdout="Monthly Revenue:\n2026-01: $1200\n2026-02: $1400",
        stderr="",
        duration_ms=500,
        cpu_usage_pct=0.2,
        memory_usage_mb=40,
        artifacts=context.artifacts,
    ))

    validator = TaskValidationAgent()
    result = await validator.validate_task(context)

    assert result.passed is True
    assert result.score == 1.0
    assert result.is_false_success is False
    assert len(result.failures) == 0


@pytest.mark.asyncio
async def test_false_success_detected_when_exit_code_zero_but_missing_chart():
    """CRITICAL TEST: Exit code 0, but no chart produced -> FALSE SUCCESS DETECTED."""
    context = TaskContext(
        task_id="test-2",
        prompt="Analyze sales.csv and generate sales_chart.png",
        plan={"expected_outputs": [{"name": "sales_chart.png", "type": "image", "required": True}]},
    )
    # No artifacts generated!
    context.artifacts = []
    context.record_execution(ExecutionRecord(
        attempt=1,
        exit_code=0,
        stdout="Calculations done, but forgot to save chart.",
        stderr="",
        duration_ms=400,
        cpu_usage_pct=0.2,
        memory_usage_mb=40,
        artifacts=[],
    ))

    validator = TaskValidationAgent()
    result = await validator.validate_task(context)

    assert result.passed is False
    assert result.is_false_success is True
    assert "FALSE SUCCESS DETECTED" in result.explanation
    assert any("sales_chart.png" in f for f in result.failures)
