"""Master Agent Orchestrator: Supervisory Intelligence and Lifecycle Controller."""
import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.coding.agent import CodingAgent
from app.agents.master.context import (
    ErrorRecord,
    ExecutionRecord,
    RepairRecord,
    TaskContext,
    ValidationRecord,
)
from app.agents.master.state_machine import TaskStateMachine
from app.agents.planner.agent import PlannerAgent
from app.agents.recovery.agent import RecoveryAgent
from app.agents.validator.agent import TaskValidationAgent
from app.core.config import settings
from app.core.events import event_bus
from app.core.logging import logger
from app.database.models import TaskModel
from app.database.repositories import TaskRepository
from app.execution.engine import ExecutionEngine
from app.schemas.enums import AgentType, ErrorType, EventType, FinalStatus, NetworkPolicy, TaskState
from app.security.policy import SecurityPolicyEngine


class MasterAgentOrchestrator:
    """
    Central Supervising Intelligence of the ReRun Platform.
    Enforces the bounded autonomous loop and coordinates specialized agents.
    """

    def __init__(
        self,
        task_id: str,
        prompt: str,
        db_session: Optional[AsyncSession] = None,
        max_retries: Optional[int] = None,
        network_policy: NetworkPolicy = NetworkPolicy.DISABLED,
        initial_files: Optional[List[str]] = None,
    ):
        self.task_id = task_id
        self.prompt = prompt
        self.db_session = db_session
        self.repo = TaskRepository(db_session) if db_session else None
        self.max_retries = max_retries or settings.MAX_RETRIES
        self.network_policy = network_policy
        self.initial_files = initial_files or []

        # Master-managed Context & State Machine
        self.context = TaskContext(
            task_id=task_id,
            prompt=prompt,
            max_retries=self.max_retries,
            files_available=self.initial_files,
        )
        self.fsm = TaskStateMachine(initial_state=TaskState.RECEIVED)

        # Specialized Agent Subsystems
        self.planner = PlannerAgent()
        self.coder = CodingAgent()
        self.security = SecurityPolicyEngine(network_policy=self.network_policy)
        self.executor = ExecutionEngine()
        self.recovery = RecoveryAgent()
        self.validator = TaskValidationAgent()

        self._cancelled = False

    async def cancel(self, reason: str = "User cancellation requested"):
        """Human override to cancel execution from any active state."""
        self._cancelled = True
        if not self.fsm.is_terminal:
            self._transition(TaskState.CANCELLED, reason=reason)
            await self._record_and_publish(
                EventType.TASK_CANCELLED,
                {"reason": reason, "status": FinalStatus.CANCELLED.value},
            )
            if self.repo:
                await self.repo.update_task_state(
                    task_id=self.task_id,
                    state=TaskState.CANCELLED,
                    final_status=FinalStatus.CANCELLED.value,
                )

    def _transition(self, target_state: TaskState, reason: str = ""):
        """Transitions state machine and syncs context."""
        log = self.fsm.transition(
            target_state=target_state,
            attempt=self.context.current_attempt,
            agent_responsible="master_agent",
            reason=reason,
        )
        self.context.current_state = target_state
        logger.info(f"Task {self.task_id} FSM: {log.from_state.value} -> {log.to_state.value} ({reason})")

    async def _record_and_publish(
        self,
        event_type: EventType,
        details: Optional[Dict[str, Any]] = None,
        agent_name: str = "master_agent",
    ):
        """Emits event to EventBus for real-time WebSocket distribution and persists to DB."""
        payload = {
            "task_id": self.task_id,
            "type": event_type.value,
            "state": self.context.current_state.value,
            "attempt": self.context.current_attempt,
            "agent": agent_name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details or {},
        }
        await event_bus.publish(self.task_id, payload)

        if self.repo:
            try:
                await self.repo.record_task_event(
                    task_id=self.task_id,
                    event_type=event_type.value,
                    attempt=self.context.current_attempt,
                    agent_name=agent_name,
                    details=details or {},
                )
                await self.repo.update_task_state(
                    task_id=self.task_id,
                    state=self.context.current_state,
                    attempt=self.context.current_attempt,
                )
            except Exception as e:
                logger.error(f"Error persisting event to DB: {e}")

    async def run(self) -> Dict[str, Any]:
        """
        Executes the autonomous loop:
        PLAN -> GENERATE -> SECURE -> EXECUTE -> OBSERVE -> DIAGNOSE/REPAIR -> VALIDATE
        """
        start_time = time.time()
        await self._record_and_publish(EventType.TASK_CREATED, {"prompt": self.prompt})

        # Ensure task workspace is clean and isolated
        task_workspace = settings.WORKSPACE_DIR / self.task_id
        if task_workspace.exists():
            import shutil
            shutil.rmtree(task_workspace)
        task_workspace.mkdir(parents=True, exist_ok=True)

        try:
            # 1. PLANNING STAGE
            if self._cancelled:
                return self.context.to_summary_dict()

            self._transition(TaskState.PLANNING, reason="Master requests structured plan")
            await self._record_and_publish(EventType.PLANNING_STARTED, {}, AgentType.PLANNER.value)

            plan_out = await self.planner.plan(
                task_prompt=self.prompt,
                available_files=self.context.files_available,
            )
            self.context.plan = plan_out.model_dump()
            if self.repo:
                await self.repo.record_plan(
                    task_id=self.task_id,
                    goal=plan_out.goal,
                    subtasks=[s.model_dump() for s in plan_out.subtasks],
                    dependencies=plan_out.dependencies,
                    expected_outputs=[o.model_dump() for o in plan_out.expected_outputs],
                    validation_requirements=plan_out.validation_requirements,
                    constraints=plan_out.constraints,
                    raw_plan=self.context.plan,
                )

            self._transition(TaskState.PLAN_READY, reason="Plan validated by Master")
            await self._record_and_publish(
                EventType.PLAN_GENERATED,
                {"plan": self.context.plan},
                AgentType.PLANNER.value,
            )

            # 2. CODE GENERATION STAGE
            self._transition(TaskState.GENERATING, reason="Master delegates to Coding Agent")
            code_payload = await self.coder.generate_code(
                task_prompt=self.prompt,
                plan=self.context.plan,
                available_files=self.context.files_available,
            )

            cv = self.context.add_code_version(
                source_code=code_payload.code,
                entrypoint=code_payload.entrypoint,
                dependencies=code_payload.dependencies,
                agent="coding_agent",
                modification_reason="Initial generation from plan",
            )
            if self.repo:
                await self.repo.record_code_version(
                    task_id=self.task_id,
                    version=cv.version,
                    version_tag=cv.version_tag,
                    source_code=cv.source_code,
                    entrypoint=cv.entrypoint,
                    dependencies=cv.dependencies,
                    agent_name=cv.agent,
                    parent_version=cv.parent_version,
                    modification_reason=cv.modification_reason,
                    diff_from_parent=cv.diff_from_parent,
                )

            await self._record_and_publish(
                EventType.CODE_GENERATED,
                {"version": cv.version_tag, "entrypoint": cv.entrypoint},
                AgentType.CODING.value,
            )

            # 3. SUPERVISED EXECUTION & RECOVERY LOOP
            while not self.fsm.is_terminal and not self._cancelled:
                # --- A. SECURITY CHECK STAGE ---
                self._transition(TaskState.SECURITY_CHECK, reason="Static policy verification")
                await self._record_and_publish(EventType.SECURITY_CHECK_STARTED, {}, AgentType.SECURITY.value)

                current_code = self.context.get_latest_code()
                sec_report = self.security.inspect_code(current_code.source_code)

                if not sec_report.allowed:
                    # Hard stop on security violation
                    self._transition(TaskState.BLOCKED, reason=f"Violations: {'; '.join(sec_report.violations)}")
                    await self._record_and_publish(
                        EventType.SECURITY_VIOLATION,
                        sec_report.to_dict(),
                        AgentType.SECURITY.value,
                    )
                    self._transition(TaskState.FAILED, reason="Execution blocked by security policy")
                    if self.repo:
                        await self.repo.update_task_state(
                            task_id=self.task_id,
                            state=TaskState.FAILED,
                            final_status=FinalStatus.BLOCKED_BY_SECURITY.value,
                            error_message="; ".join(sec_report.violations),
                        )
                    break

                await self._record_and_publish(
                    EventType.SECURITY_CHECK_PASSED,
                    {"risk_level": sec_report.risk_level},
                    AgentType.SECURITY.value,
                )

                # --- B. SANDBOX EXECUTION STAGE ---
                self._transition(TaskState.EXECUTING, reason="Executing code in sandbox")
                await self._record_and_publish(
                    EventType.SANDBOX_STARTED,
                    {"attempt": self.context.current_attempt, "entrypoint": current_code.entrypoint},
                    AgentType.SANDBOX.value,
                )

                raw_exec = await self.executor.execute_code(
                    task_id=self.task_id,
                    code=current_code.source_code,
                    entrypoint=current_code.entrypoint,
                    initial_files=self.context.files_available,
                    network_policy=self.network_policy,
                )

                # Update context artifacts
                self.context.artifacts = raw_exec.get("artifacts", [])
                if self.repo:
                    for art in self.context.artifacts:
                        await self.repo.record_artifact(
                            task_id=self.task_id,
                            filename=art["filename"],
                            file_type=art["file_type"],
                            file_size_bytes=art["file_size_bytes"],
                            storage_path=art["storage_path"],
                            sha256_hash=art.get("sha256_hash"),
                        )

                # Check Timeout condition
                if raw_exec.get("timeout"):
                    self._transition(TaskState.TIMEOUT, reason="Execution time limit exceeded")
                    await self._record_and_publish(EventType.TIMEOUT_DETECTED, {"timeout": True})

                    # Record execution and error so context and recovery agent have complete visibility
                    exec_rec = ExecutionRecord(
                        attempt=self.context.current_attempt,
                        exit_code=raw_exec.get("exit_code", 124),
                        stdout=raw_exec.get("stdout", ""),
                        stderr=raw_exec.get("stderr", ""),
                        duration_ms=raw_exec.get("duration_ms", 0.0),
                        cpu_usage_pct=raw_exec.get("cpu_usage_pct", 0.0),
                        memory_usage_mb=raw_exec.get("memory_usage_mb", 0.0),
                        artifacts=raw_exec.get("artifacts", []),
                        oom_killed=False,
                        timeout=True,
                    )
                    self.context.record_execution(exec_rec)
                    self.context.record_error(
                        ErrorRecord(
                            attempt=self.context.current_attempt,
                            error_type=ErrorType.TIMEOUT,
                            error_message=raw_exec.get("stderr", "Execution timed out"),
                            traceback_clean=raw_exec.get("stderr", "Execution timed out"),
                        )
                    )
                    if self.repo:
                        await self.repo.record_execution(
                            task_id=self.task_id,
                            code_version_id=None,
                            attempt=self.context.current_attempt,
                            exit_code=raw_exec.get("exit_code", 124),
                            stdout=raw_exec.get("stdout", ""),
                            stderr=raw_exec.get("stderr", ""),
                            duration_ms=raw_exec.get("duration_ms", 0.0),
                            cpu_usage_pct=raw_exec.get("cpu_usage_pct", 0.0),
                            memory_usage_mb=raw_exec.get("memory_usage_mb", 0.0),
                            oom_killed=False,
                            timeout=True,
                        )

                    # First-class Master Timeout Decision:
                    if self.context.current_attempt < self.max_retries:
                        logger.info("Master decides: Optimize algorithm to resolve timeout")
                        self._transition(TaskState.REPAIRING, reason="Master requests optimization for timeout")
                        # Stage repair
                        recovery_decision = await self.recovery.diagnose_and_repair(self.context)
                        self._stage_repair(recovery_decision)
                        continue
                    else:
                        logger.warning("Repeated timeout exceeded maximum retries. Halting task.")
                        self._transition(TaskState.FAILED, reason="Repeated timeout limit reached")
                        if self.repo:
                            await self.repo.update_task_state(
                                task_id=self.task_id,
                                state=TaskState.FAILED,
                                final_status=FinalStatus.TIMEOUT.value,
                            )
                        break

                # --- C. OBSERVATION STAGE ---
                self._transition(TaskState.OBSERVING, reason="Master inspects runtime outputs")
                from app.observation.observer import RuntimeObserver
                obs = RuntimeObserver.observe(raw_exec)

                # Record execution in context and DB
                exec_rec = ExecutionRecord(
                    attempt=self.context.current_attempt,
                    exit_code=obs.exit_code,
                    stdout=obs.stdout,
                    stderr=obs.stderr,
                    duration_ms=obs.duration_ms,
                    cpu_usage_pct=obs.cpu_usage_pct,
                    memory_usage_mb=obs.memory_usage_mb,
                    artifacts=obs.artifacts,
                    oom_killed=obs.oom_killed,
                    timeout=obs.timeout,
                )
                self.context.record_execution(exec_rec)
                if self.repo:
                    await self.repo.record_execution(
                        task_id=self.task_id,
                        code_version_id=None,
                        attempt=self.context.current_attempt,
                        exit_code=obs.exit_code,
                        stdout=obs.stdout,
                        stderr=obs.stderr,
                        duration_ms=obs.duration_ms,
                        cpu_usage_pct=obs.cpu_usage_pct,
                        memory_usage_mb=obs.memory_usage_mb,
                        oom_killed=obs.oom_killed,
                        timeout=obs.timeout,
                    )

                await self._record_and_publish(
                    EventType.EXECUTION_FINISHED,
                    obs.to_dict(),
                    AgentType.OBSERVER.value,
                )

                # --- D. MASTER AGENT DECISION JUNCTION ---
                if obs.exit_code == 0:
                    # Program exited cleanly -> Proceed to Task Validation
                    self._transition(TaskState.VALIDATING, reason="Execution exited 0, running task validation")
                    await self._record_and_publish(EventType.VALIDATION_STARTED, {}, AgentType.VALIDATOR.value)

                    val_res = await self.validator.validate_task(self.context)
                    val_rec = ValidationRecord(
                        attempt=self.context.current_attempt,
                        passed=val_res.passed,
                        score=val_res.score,
                        checks=[c.model_dump() for c in val_res.checks],
                        failures=val_res.failures,
                        explanation=val_res.explanation,
                        is_false_success=val_res.is_false_success,
                    )
                    self.context.record_validation(val_rec)
                    if self.repo:
                        await self.repo.record_validation(
                            task_id=self.task_id,
                            attempt=self.context.current_attempt,
                            passed=val_res.passed,
                            score=val_res.score,
                            checks=[c.model_dump() for c in val_res.checks],
                            failures=val_res.failures,
                            explanation=val_res.explanation,
                            is_false_success=val_res.is_false_success,
                        )

                    await self._record_and_publish(
                        EventType.VALIDATION_RESULT,
                        val_res.model_dump(),
                        AgentType.VALIDATOR.value,
                    )

                    if val_res.passed:
                        # SUCCESS: Both execution and task requirements satisfied!
                        self._transition(TaskState.COMPLETED, reason="Task requirements validated successfully")
                        if self.repo:
                            await self.repo.update_task_state(
                                task_id=self.task_id,
                                state=TaskState.COMPLETED,
                                final_status=FinalStatus.COMPLETED.value,
                            )
                        await self._record_and_publish(
                            EventType.TASK_COMPLETED,
                            {"score": val_res.score, "attempts": self.context.current_attempt},
                        )
                        break
                    else:
                        # False success (Exit 0, but task validation failed)
                        logger.warning(f"Task {self.task_id}: FALSE SUCCESS DETECTED. Routing to recovery.")
                        err_rec = ErrorRecord(
                            attempt=self.context.current_attempt,
                            error_type=ErrorType.OUTPUT_ERROR,
                            error_message=val_res.explanation,
                            traceback_clean="",
                        )
                        self.context.record_error(err_rec)
                        self._transition(TaskState.ANALYZING_FAILURE, reason="Task validation failed (False Success)")

                else:
                    # Non-zero exit code -> Standard Runtime Failure
                    err_rec = ErrorRecord(
                        attempt=self.context.current_attempt,
                        error_type=obs.error_type or ErrorType.LOGIC_ERROR,
                        error_message=obs.error_message or "Execution failed",
                        traceback_clean=obs.traceback_clean or "",
                        failing_line=obs.failing_line,
                    )
                    self.context.record_error(err_rec)
                    if self.repo:
                        await self.repo.record_error(
                            task_id=self.task_id,
                            execution_id=None,
                            attempt=self.context.current_attempt,
                            error_type=err_rec.error_type.value,
                            error_message=err_rec.error_message,
                            traceback_clean=err_rec.traceback_clean,
                            failing_line=err_rec.failing_line,
                        )

                    self._transition(TaskState.ANALYZING_FAILURE, reason=f"Runtime error: {err_rec.error_type.value}")
                    await self._record_and_publish(
                        EventType.FAILURE_ANALYZED,
                        {"error_type": err_rec.error_type.value, "error_message": err_rec.error_message},
                    )

                # --- E. RECOVERY & STOPPING DECISIONS ---
                if self.context.current_attempt >= self.max_retries:
                    logger.warning(f"Task {self.task_id}: Maximum retries ({self.max_retries}) exhausted.")
                    self._transition(TaskState.FAILED, reason=f"Max retries ({self.max_retries}) exceeded")
                    if self.repo:
                        await self.repo.update_task_state(
                            task_id=self.task_id,
                            state=TaskState.FAILED,
                            final_status=FinalStatus.FAILED_AFTER_RETRIES.value,
                            error_message="Maximum repair retries exhausted.",
                        )
                    await self._record_and_publish(EventType.TASK_FAILED, {"reason": "Max retries exceeded"})
                    break

                if self.context.is_repeated_failure(threshold=settings.REPEATED_FAILURE_THRESHOLD):
                    logger.warning(f"Task {self.task_id}: Repeated failure threshold hit. Triggering replanning.")
                    self._transition(TaskState.REPLANNING, reason="Repeated failure threshold exceeded")
                    # Replan subtasks
                    self._transition(TaskState.PLANNING, reason="Re-synthesizing plan due to repeated failure")
                    plan_out = await self.planner.plan(
                        task_prompt=f"{self.prompt} (Note: previous approach repeatedly failed with {self.context.last_error_signature})",
                        available_files=self.context.files_available,
                    )
                    self.context.plan = plan_out.model_dump()
                    self._transition(TaskState.PLAN_READY, reason="Revised plan ready")
                    self._transition(TaskState.GENERATING, reason="Generating new code for revised plan")
                    code_payload = await self.coder.generate_code(
                        task_prompt=self.prompt,
                        plan=self.context.plan,
                        available_files=self.context.files_available,
                    )
                    self.context.current_attempt += 1
                    self.context.add_code_version(
                        source_code=code_payload.code,
                        entrypoint=code_payload.entrypoint,
                        dependencies=code_payload.dependencies,
                        agent="coding_agent",
                        modification_reason="Re-generated code from revised plan",
                    )
                    continue

                # Standard targeted recovery
                self._transition(TaskState.REPAIRING, reason="Delegating to Recovery Agent")
                await self._record_and_publish(EventType.RECOVERY_STARTED, {}, AgentType.RECOVERY.value)

                repair_decision = await self.recovery.diagnose_and_repair(self.context)
                self.context.record_repair(RepairRecord(
                    attempt=self.context.current_attempt,
                    diagnosis=repair_decision.diagnosis,
                    error_type=repair_decision.error_type,
                    repair_strategy=repair_decision.repair_strategy,
                    confidence=repair_decision.confidence,
                    needs_replan=repair_decision.needs_replan,
                ))

                if repair_decision.needs_replan:
                    self._transition(TaskState.REPLANNING, reason="Recovery Agent requested strategy replan")
                    self._transition(TaskState.PLANNING, reason="Re-planning from recovery recommendation")
                    plan_out = await self.planner.plan(
                        task_prompt=self.prompt,
                        available_files=self.context.files_available,
                    )
                    self.context.plan = plan_out.model_dump()
                    self._transition(TaskState.PLAN_READY, reason="Revised plan ready")
                    self._transition(TaskState.GENERATING, reason="Generating code for revised plan")
                    code_payload = await self.coder.generate_code(
                        task_prompt=self.prompt,
                        plan=self.context.plan,
                        available_files=self.context.files_available,
                    )
                    self.context.current_attempt += 1
                    self.context.add_code_version(
                        source_code=code_payload.code,
                        entrypoint=code_payload.entrypoint,
                        dependencies=code_payload.dependencies,
                        agent="coding_agent",
                        modification_reason="Code re-generated following strategy replan",
                    )
                    continue

                self._stage_repair(repair_decision)

        except Exception as e:
            logger.error(f"Unexpected Master Agent orchestration exception: {e}", exc_info=True)
            if not self.fsm.is_terminal:
                self._transition(TaskState.FAILED, reason=f"Platform Error: {str(e)}")
                if self.repo:
                    await self.repo.update_task_state(
                        task_id=self.task_id,
                        state=TaskState.FAILED,
                        final_status=FinalStatus.FAILED_AFTER_RETRIES.value,
                        error_message=str(e),
                    )

        self.context.total_duration_sec = time.time() - start_time
        self.context.completed_at = datetime.now(timezone.utc).isoformat()

        # Persist final duration to DB (not covered by intermediate state updates)
        if self.repo:
            try:
                stmt = (
                    update(TaskModel)
                    .where(TaskModel.id == self.task_id)
                    .values(total_duration_sec=self.context.total_duration_sec)
                )
                await self.repo.session.execute(stmt)
                await self.repo.session.commit()
            except Exception as e:
                logger.warning(f"Could not persist total_duration_sec: {e}")

        return self.context.to_summary_dict()

    def _stage_repair(self, repair_decision):
        """Increments attempt and registers repaired code version."""
        self.context.current_attempt += 1
        # Use the current code version's entrypoint — don't assume main.py
        current_code = self.context.get_latest_code()
        current_entrypoint = current_code.entrypoint if current_code else "main.py"
        new_cv = self.context.add_code_version(
            source_code=repair_decision.modified_code,
            entrypoint=current_entrypoint,
            dependencies=repair_decision.dependencies,
            agent="recovery_agent",
            modification_reason=f"Repair {repair_decision.error_type.value}: {repair_decision.repair_strategy}",
        )
        self._transition(
            TaskState.RETRYING,
            reason=f"Staging attempt_{new_cv.version} with repaired code",
        )
