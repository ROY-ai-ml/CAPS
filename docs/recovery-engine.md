# Runtime-Guided Adaptive Recovery Engine

## 1. Differentiated Recovery vs. Blind Regeneration

Most existing coding agents implement a naive recovery loop:
```python
if error:
    prompt = f"Here is the error: {stderr}. Please fix it."
    code = llm.generate(prompt)
```
This naive approach frequently fails because:
1. LLMs hallucinate unrelated rewrites that break working sections of code.
2. Circular error loops occur where the LLM oscillates between two incorrect syntax variants.
3. Complex errors (e.g. DataFrame column casing or OOM) require specialized remediation strategies.

ReRun replaces this with **Differentiated, Targeted Recovery**.

---

## 2. 15-Class Error Taxonomy

The runtime observer deterministically categorizes failures into 15 distinct classes:

| Class | Trigger / Pattern | Targeted Remediation Strategy |
|---|---|---|
| `SYNTAX_ERROR` | `SyntaxError`, `IndentationError` | AST token inspection and minimal punctuation correction. |
| `KEY_ERROR` | `KeyError` (common in pandas DataFrames) | Column normalization (`df.columns.str.lower()`) and dynamic column matching. |
| `IMPORT_ERROR` | `ModuleNotFoundError`, `ImportError` | Replace with standard library equivalent or approved dependency. |
| `TIMEOUT` | Duration > 30s, exit code 124 | Replace nested loops with vectorized NumPy/Pandas operations or chunked streams. |
| `MEMORY_LIMIT` | OOM killed, exit code 137 | Stream processing, downcasting datatypes, deleting intermediate matrices. |
| `FILE_ERROR` | `FileNotFoundError` | Defensive file presence checks and automatic mock generation. |
| `OUTPUT_ERROR` | Missing expected deliverable (False Success) | Inject explicit `plt.savefig()` or file write call with requested path. |
| `SECURITY_VIOLATION` | Prohibited import or syscall | Hard stop; terminates task immediately. |

---

## 3. Anti-Looping & Repeated Failure Avoidance

The Master Agent maintains `TaskContext.repeated_error_counts` and `consecutive_identical_errors`.

If the same error signature recurs consecutively:
1. The Master Agent flags `is_repeated_failure() == True`.
2. The Recovery Agent receives a critical alert:
   ```text
   REPEATED FAILURE DETECTED: The last 2 attempts failed with KeyError.
   Do not repeat the previous patch. Implement an alternative strategy or request replanning.
   ```
3. If the Recovery Agent signals `needs_replan: True`, the Master Agent transitions to `REPLANNING`, triggering the Planner Agent to decompose the subtasks differently.
