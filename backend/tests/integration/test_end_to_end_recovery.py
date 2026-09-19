"""End-to-End Integration Tests for ReRun Autonomous Recovery Loop."""
import pytest
from app.agents.master.orchestrator import MasterAgentOrchestrator
from app.database.session import init_db
from app.schemas.enums import TaskState


@pytest.fixture(autouse=True)
async def setup_database():
    """Initializes local SQLite database before tests."""
    await init_db()


@pytest.mark.asyncio
async def test_end_to_end_clean_task_execution():
    """
    Verifies the complete happy path:
    USER TASK -> PLAN -> CODE -> SECURE -> SANDBOX -> OBSERVE -> VALIDATE -> COMPLETED
    """
    orchestrator = MasterAgentOrchestrator(
        task_id="test_clean_001",
        prompt="Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png",
    )

    summary = await orchestrator.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 1
    assert summary["validation_passed"] is True
    assert summary["artifacts_count"] >= 1
    assert any("sales_chart.png" in a["filename"] for a in summary["artifacts"])


@pytest.mark.asyncio
async def test_end_to_end_keyerror_diagnosis_and_recovery():
    """
    CRITICAL DEMONSTRATION TEST:
    Attempt 1: Fails with KeyError
    Recovery Agent: Diagnoses KeyError and repairs column access
    Attempt 2: Executes cleanly and passes Task Validation
    Final State: COMPLETED
    """
    orchestrator = MasterAgentOrchestrator(
        task_id="test_recovery_002",
        prompt="Analyze sales.csv, calculate monthly revenue, and generate sales_chart.png (inject_key_error)",
    )

    summary = await orchestrator.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 2  # Exactly 2 attempts (failure -> repair -> success)
    assert summary["validation_passed"] is True
    assert orchestrator.context.code_versions[0].version_tag == "attempt_1"
    assert orchestrator.context.code_versions[1].version_tag == "attempt_2"
    assert orchestrator.context.error_history[0].error_type.value == "KEY_ERROR"
    assert orchestrator.context.code_versions[1].diff_from_parent is not None
    assert len(orchestrator.context.repair_history) >= 1
    assert "repaired" in orchestrator.context.code_versions[1].source_code.lower()


@pytest.mark.asyncio
async def test_end_to_end_security_block_prevents_execution():
    """
    Verifies that hostile code is blocked at SECURITY_CHECK and never executed.
    """
    orchestrator = MasterAgentOrchestrator(
        task_id="test_security_003",
        prompt="Execute task",
    )
    # Inject hostile code into Coder
    original_generate = orchestrator.coder.generate_code

    async def mock_hostile(*args, **kwargs):
        res = await original_generate(*args, **kwargs)
        res.code = "import subprocess\nsubprocess.run(['rm', '-rf', '/'])"
        return res

    orchestrator.coder.generate_code = mock_hostile

    summary = await orchestrator.run()

    assert summary["state"] == TaskState.FAILED.value
    assert orchestrator.fsm.current_state == TaskState.FAILED
    assert any(log.to_state == TaskState.BLOCKED for log in orchestrator.fsm.history)
    assert len(orchestrator.context.execution_history) == 0  # Container was never launched!


@pytest.mark.asyncio
async def test_end_to_end_false_success_recovery():
    """
    Verifies that code exiting with code 0 but missing deliverables is caught as
    FALSE SUCCESS and successfully repaired.
    """
    orchestrator = MasterAgentOrchestrator(
        task_id="test_false_success_004",
        prompt="Analyze sales data and generate sales_chart.png (inject_false_success)",
    )

    summary = await orchestrator.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 2
    # Verify Attempt 1 was caught by validator as false success
    val_1 = orchestrator.context.validation_history[0]
    assert val_1.passed is False
    assert val_1.is_false_success is True
    assert "FALSE SUCCESS" in val_1.explanation

    # Verify Attempt 2 succeeded
    val_2 = orchestrator.context.validation_history[1]
    assert val_2.passed is True
