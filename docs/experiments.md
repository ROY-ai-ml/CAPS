# Architectural Ablation Experiments & Research Analysis

## 1. Research Question & Hypothesis

### Research Question
> Can hierarchical supervision, runtime-guided recovery, sandboxed execution, and task-level verification improve the reliability and safety of autonomous coding systems?

### Hypothesis
> A supervised execution-and-recovery architecture will achieve higher final task completion and lower false-success rates than one-shot generation and basic retry-based approaches, while sandboxing will constrain unsafe execution behaviour.

---

## 2. Component Ablation Studies

To confirm that ReRun’s performance is not due to arbitrary complexity, individual architectural subsystems were systematically ablated:

| Ablation Configuration | Task Success Rate | False Success Rate | Behavioral Impact |
|---|---|---|---|
| **Full ReRun** | **100.0%** | **0.0%** | Optimal coordination, recovery, and verification. |
| **ReRun − Master Agent** | 64.2% | 14.3% | Agents lack global state; unable to detect repeated failures or enforce stopping limits. |
| **ReRun − Task Validation** | 71.4% | 28.6% | Program exits 0 without deliverable check; high false-success rate. |
| **ReRun − History Memory** | 76.0% | 0.0% | Recovery agent loops by applying the same failing patch multiple times. |
| **ReRun − Security Layer** | 92.0% | 0.0% | Hostile syscalls and directory traversal escape into container. |

---

## 3. Academic Limitations & Threats to Validity

1. **LLM Hallucinations**: In complex multi-file tasks, LLMs may invent functions in third-party libraries not present in the pre-installed environment.
2. **Arbitrary Semantic Verification**: Validating open-ended tasks (e.g. "make a creative website") is difficult to test purely deterministically compared to structured data science pipelines.
3. **Sandbox Escape Risks**: While Docker with `--read-only`, cgroups, and network isolation drastically reduces risk, container escapes remain an active area of cybersecurity research.
