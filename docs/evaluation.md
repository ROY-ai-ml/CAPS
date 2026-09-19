# ReRun Evaluation Framework & Benchmark Methodology

## 1. Experimental Methodology

The evaluation methodology rigorously tests autonomous coding reliability across four key dimensions:

1. **Reliability**: First Attempt Success Rate vs. Final Task Success Rate (demonstrating recovery power).
2. **Verification Accuracy**: False Success Rate (detecting programs that exit cleanly with code 0 but omit deliverables).
3. **Safety & Containment**: Blocked Unsafe Executions (filtering prohibited syscalls and path traversal).
4. **Efficiency**: Average number of repair attempts per task and execution latency.

---

## 2. Experimental Results Summary

Empirical results from the 7-task benchmark suite (`evaluation/benchmark_report.json`):

| System Configuration | Final Success Rate | First Attempt Success | Avg Attempts | False Success Rate |
|---|---|---|---|---|
| **Baseline A (One-Shot LLM)** | 85.7% | 85.7% | 1.00 | **14.3%** |
| **Baseline B (Simple Retry)** | 85.7% | 85.7% | 1.29 | **14.3%** |
| **ReRun (Proposed Architecture)** | **100.0%** | 85.7% | 1.29 | **0.0%** |

### Key Findings:
1. **False Success Vulnerability**: Both Baseline A and Baseline B suffered a **14.3% False Success Rate**, because they accepted exit code `0` as completion without verifying deliverable presence.
2. **Elimination of False Successes**: ReRun achieved a **0.0% False Success Rate** because the Task Validation Agent checked the physical generation of `sales_chart.png` and routed missing deliverables to targeted repair.
3. **Autonomous Self-Correction**: When given deliberate errors (e.g. `KeyError`), ReRun successfully diagnosed the schema issue and resolved it on Attempt 2 without human intervention.
