# ReRun Agent Hierarchy & Design Specification

## 1. Multi-Agent Hierarchy Overview

ReRun employs a strict separation of concerns across specialized agents, preventing monolithic prompts where a single LLM attempts to plan, code, supervise, and grade itself.

| Agent | Core Responsibility | Input | Primary Output |
|---|---|---|---|
| **Master Agent** | Supervising intelligence, state flow, lifecycle control | User prompt, task state, observations | Lifecycle transitions, recovery routing |
| **Planner Agent** | Problem decomposition, subtasks, dependencies | Objective, workspace files, constraints | Structured JSON Execution Plan |
| **Coding Agent** | Synthesis of standalone executable Python 3.10 code | Task, plan, files, dependencies | Python source, entrypoint, deliverables |
| **Recovery Agent** | History-aware root cause diagnosis and targeted repair | Stack trace, past attempts, code diffs | Diagnosis, repair strategy, patched code |
| **Task Validator** | Semantic deliverable evaluation & false-success check | Prompt, plan, artifacts, runtime stdout | Validation verdict, score, failure checklist |

---

## 2. Master Agent Decision Policies

The Master Agent operates on clear decision logic:

```python
if security_violation:
    transition(BLOCKED) -> transition(FAILED)
elif timeout_detected:
    if attempt < max_retries:
        transition(REPAIRING) # Algorithmic optimization
    else:
        transition(FAILED)
elif execution_failed:
    if attempt >= max_retries:
        transition(FAILED) # Stopping condition reached
    elif is_repeated_failure():
        transition(REPLANNING) # Avoid looping on identical fix
    else:
        transition(REPAIRING) # Standard targeted repair
elif execution_success (exit_code == 0):
    run_task_validation()
    if validation.passed:
        transition(COMPLETED)
    else:
        # False Success Detected!
        record_error(OUTPUT_ERROR, validation.explanation)
        transition(ANALYZING_FAILURE) -> transition(REPAIRING)
```

---

## 3. History-Aware Execution Memory

The Recovery Agent does not merely receive raw stderr. It consumes the complete `TaskContext` trajectory:

```text
Attempt 1:
  Code: df['Total_Revenue_Amount'].sum()
  Error: KeyError: 'Total_Revenue_Amount'
  Repair: Changed column casing to lowercase

Attempt 2:
  Code: df['total_revenue_amount'].sum()
  Error: KeyError: 'total_revenue_amount'

--> Repeated failure detected on KeyError!
--> Anti-looping trigger: Do not repeat lowercase patch.
--> Strategy change: Inspect df.columns dynamically.
```

This prevents the circular debugging loops common in naive retry agents.
