"""Unit Tests for 17-State Finite State Machine."""
import pytest
from app.agents.master.state_machine import IllegalStateTransitionError, TaskStateMachine
from app.schemas.enums import TaskState


def test_valid_happy_path_transitions():
    """Verifies standard linear progression from RECEIVED to COMPLETED."""
    fsm = TaskStateMachine()
    assert fsm.current_state == TaskState.RECEIVED

    fsm.transition(TaskState.PLANNING, reason="Master starts planning")
    assert fsm.current_state == TaskState.PLANNING

    fsm.transition(TaskState.PLAN_READY, reason="Plan created")
    assert fsm.current_state == TaskState.PLAN_READY

    fsm.transition(TaskState.GENERATING, reason="Coder starts generation")
    assert fsm.current_state == TaskState.GENERATING

    fsm.transition(TaskState.SECURITY_CHECK, reason="Code generated, check policy")
    assert fsm.current_state == TaskState.SECURITY_CHECK

    fsm.transition(TaskState.EXECUTING, reason="Policy passed, run in sandbox")
    assert fsm.current_state == TaskState.EXECUTING

    fsm.transition(TaskState.OBSERVING, reason="Execution done, collect output")
    assert fsm.current_state == TaskState.OBSERVING

    fsm.transition(TaskState.VALIDATING, reason="Master sees exit code 0, validate task")
    assert fsm.current_state == TaskState.VALIDATING

    fsm.transition(TaskState.COMPLETED, reason="Semantic checks passed")
    assert fsm.current_state == TaskState.COMPLETED
    assert fsm.is_terminal is True


def test_illegal_transition_rejection():
    """Verifies that unauthorized state jumps raise IllegalStateTransitionError."""
    fsm = TaskStateMachine()
    with pytest.raises(IllegalStateTransitionError):
        fsm.transition(TaskState.COMPLETED, reason="Cannot skip directly to completed")


def test_timeout_first_class_transitions():
    """Verifies first-class timeout recovery options: REPAIRING, REPLANNING, FAILED."""
    # Option 1: Optimize code
    fsm1 = TaskStateMachine()
    fsm1.transition(TaskState.PLANNING)
    fsm1.transition(TaskState.PLAN_READY)
    fsm1.transition(TaskState.GENERATING)
    fsm1.transition(TaskState.SECURITY_CHECK)
    fsm1.transition(TaskState.EXECUTING)
    fsm1.transition(TaskState.TIMEOUT, reason="Execution exceeded 30s")
    assert fsm1.current_state == TaskState.TIMEOUT
    fsm1.transition(TaskState.REPAIRING, reason="Master decides to optimize algorithm")
    assert fsm1.current_state == TaskState.REPAIRING

    # Option 2: Repeated timeout -> FAILED
    fsm2 = TaskStateMachine()
    fsm2.transition(TaskState.PLANNING)
    fsm2.transition(TaskState.PLAN_READY)
    fsm2.transition(TaskState.GENERATING)
    fsm2.transition(TaskState.SECURITY_CHECK)
    fsm2.transition(TaskState.EXECUTING)
    fsm2.transition(TaskState.TIMEOUT, reason="Execution exceeded 30s")
    fsm2.transition(TaskState.FAILED, reason="Repeated timeout limit exceeded")
    assert fsm2.current_state == TaskState.FAILED
    assert fsm2.is_terminal is True


def test_hard_security_boundary():
    """Verifies security violation transitions to BLOCKED then FAILED (hard stop)."""
    fsm = TaskStateMachine()
    fsm.transition(TaskState.PLANNING)
    fsm.transition(TaskState.PLAN_READY)
    fsm.transition(TaskState.GENERATING)
    fsm.transition(TaskState.SECURITY_CHECK)
    fsm.transition(TaskState.BLOCKED, reason="Attempted os.system shell call")
    assert fsm.current_state == TaskState.BLOCKED
    fsm.transition(TaskState.FAILED, reason="Terminated due to security policy")
    assert fsm.current_state == TaskState.FAILED


def test_user_cancellation_from_any_active_state():
    """Verifies human override cancellation is allowed from intermediate states."""
    fsm = TaskStateMachine()
    fsm.transition(TaskState.PLANNING)
    fsm.transition(TaskState.CANCELLED, reason="User clicked cancel")
    assert fsm.current_state == TaskState.CANCELLED
    assert fsm.is_terminal is True


def test_terminal_states_cannot_transition():
    """Verifies no further transitions can be made once terminal."""
    fsm = TaskStateMachine()
    fsm.transition(TaskState.PLANNING)
    fsm.transition(TaskState.PLAN_READY)
    fsm.transition(TaskState.GENERATING)
    fsm.transition(TaskState.SECURITY_CHECK)
    fsm.transition(TaskState.EXECUTING)
    fsm.transition(TaskState.OBSERVING)
    fsm.transition(TaskState.VALIDATING)
    fsm.transition(TaskState.COMPLETED)
    assert fsm.is_terminal is True

    with pytest.raises(IllegalStateTransitionError):
        fsm.transition(TaskState.PLANNING)
