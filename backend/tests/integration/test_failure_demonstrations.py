"""Section 45: Comprehensive Failure Demonstration Test Suite.

Demonstrates all 6 deliberate failure and recovery scenarios:
  Case 1: Syntax Error Recovery
  Case 2: Runtime Error (KeyError) Recovery
  Case 3: Timeout Recovery
  Case 4: Resource Violation / Memory Limit Containment
  Case 5: Security Policy Violation Hard Block
  Case 6: False-Success Detection & Deliverable Recovery
"""
import pytest
from app.agents.master.orchestrator import MasterAgentOrchestrator
from app.database.session import init_db
from app.schemas.enums import ErrorType, FinalStatus, TaskState


@pytest.fixture(autouse=True)
async def setup_db():
    await init_db()


@pytest.mark.asyncio
async def test_case_1_syntax_error_recovery():
    """Case 1: Syntax Error -> Diagnose -> Repair -> Retry -> Success."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_1_syntax",
        prompt="Analyze sales.csv and plot chart (inject_syntax_error)",
    )
    summary = await orch.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 2
    assert orch.context.error_history[0].error_type == ErrorType.SYNTAX_ERROR
    assert orch.context.validation_history[-1].passed is True


@pytest.mark.asyncio
async def test_case_2_runtime_error_keyerror_recovery():
    """Case 2: Runtime Error (KeyError) -> Diagnose -> Column Normalization Repair -> Retry -> Success."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_2_keyerror",
        prompt="Analyze sales.csv and plot chart (inject_key_error)",
    )
    summary = await orch.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 2
    assert orch.context.error_history[0].error_type == ErrorType.KEY_ERROR
    assert "repaired" in orch.context.code_versions[1].source_code.lower()


@pytest.mark.asyncio
async def test_case_3_timeout_first_class_recovery():
    """Case 3: Timeout -> Terminate -> Classify Timeout -> Master Optimize Decision -> Retry -> Success."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_3_timeout",
        prompt="Analyze sales data (inject_timeout)",
    )
    summary = await orch.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] in [2, 3]
    # Verify FSM went through TIMEOUT state
    assert any(log.to_state == TaskState.TIMEOUT for log in orch.fsm.history)


@pytest.mark.asyncio
async def test_case_4_resource_violation_containment():
    """Case 4: Resource limit exceeded -> Terminate -> Record violation -> Graceful state transition."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_4_oom",
        prompt="Analyze data",
    )
    # Simulate an OOM killed run on Attempt 1
    original_exec = orch.executor.execute_code

    async def mock_oom(*args, **kwargs):
        return {
            "status": "failed",
            "exit_code": 137,
            "stdout": "",
            "stderr": "Killed: Out of memory",
            "duration_ms": 1200,
            "cpu_usage_pct": 0.9,
            "memory_usage_mb": 512.0,
            "oom_killed": True,
            "timeout": False,
            "artifacts": [],
            "runner": "local_isolated_fallback",
        }

    orch.executor.execute_code = mock_oom
    orch.max_retries = 1

    summary = await orch.run()

    assert summary["state"] == TaskState.FAILED.value
    assert orch.context.error_history[0].error_type == ErrorType.MEMORY_LIMIT
    assert orch.context.execution_history[0].oom_killed is True


@pytest.mark.asyncio
async def test_case_5_security_violation_hard_stop():
    """Case 5: Unsafe code -> Policy check -> Hard Block -> Never executes in sandbox."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_5_security",
        prompt="Run unauthorized script",
    )
    # Inject hostile code into Coding Agent
    original_generate = orch.coder.generate_code

    async def mock_hostile(*args, **kwargs):
        res = await original_generate(*args, **kwargs)
        res.code = "import subprocess\nsubprocess.call(['whoami'])"
        return res

    orch.coder.generate_code = mock_hostile
    summary = await orch.run()

    assert summary["state"] == TaskState.FAILED.value
    assert orch.fsm.current_state == TaskState.FAILED
    assert any(log.to_state == TaskState.BLOCKED for log in orch.fsm.history)
    assert len(orch.context.execution_history) == 0  # Crucial: Code was NEVER executed


@pytest.mark.asyncio
async def test_case_6_false_success_semantic_recovery():
    """Case 6: Exit code 0 with missing chart -> Semantic Validation catches False Success -> Re-executes -> Success."""
    orch = MasterAgentOrchestrator(
        task_id="demo_case_6_false_success",
        prompt="Analyze sales data and generate sales_chart.png (inject_false_success)",
    )
    summary = await orch.run()

    assert summary["state"] == TaskState.COMPLETED.value
    assert summary["total_attempts"] == 2
    # Verify Attempt 1 was classified as false success
    assert orch.context.validation_history[0].is_false_success is True
    assert orch.context.validation_history[0].passed is False
    # Verify Attempt 2 passed validation
    assert orch.context.validation_history[1].passed is True
