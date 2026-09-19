# Sandbox Architecture & Defense-in-Depth Security

## 1. Security Philosophy: Code is Untrusted

ReRun treats all LLM-generated Python code as inherently untrusted. Security is implemented across five defensive layers.

```text
Generated Code 
      ↓ [Layer 1: Static Policy (AST inspection, forbidden imports/calls)]
Pre-Execution Check
      ↓ [Layer 2: Docker Container Isolation (read-only root, no-new-privileges)]
Docker Container
      ↓ [Layer 3: Kernel Cgroups (CPU quotas, memory caps, pids-limit)]
Resource Watchdog
      ↓ [Layer 4: Network Isolation (--network none)]
Network Gatekeeper
      ↓ [Layer 5: Output Stream Watchdog (max stdout/stderr & disk quota)]
Observer Capture
```

---

## 2. Multi-Layered Defensive Controls

### Layer 1: Deterministic AST Static Policy Engine
Before code reaches a compiler or interpreter, the static engine traverses its Abstract Syntax Tree (AST):
- **Forbidden Modules**: Blocks `subprocess`, `pty`, `posix_spawn`, `ctypes`, `winreg`, `importlib`.
- **Prohibited Calls**: Blocks `eval`, `exec`, `compile`, `__import__`, `globals()`, `os.system`, `os.popen`, `os.remove`, `os.kill`, `os.fork`.
- **Path Traversal Guard**: Detects path string literals attempting to escape the workspace (`..`, `/etc`, `/root`, `C:\Windows`).
- **Network Egress Guard**: Rejects socket or HTTP imports when policy is `DISABLED`.

### Layer 2: Docker Container Isolation (Primary Execution Boundary)
- **Container Lifecycle**: Disposable containers are created per execution and destroyed immediately after output collection.
- **Filesystem Hardening**: Root filesystem mounted with `--read-only`.
- **Temporary Mounts**: `/tmp` is an isolated tmpfs with `noexec,nosuid`. The task workspace is mounted as an ephemeral directory.

### Layer 3: Kernel Cgroups & Resource Quotas
- **Memory Cap**: `--memory=512m` and `--memory-swap=512m`. The Linux OOM killer halts memory runaway with exit code `137`.
- **CPU Quota**: `--cpus=1.0` prevents CPU thread starvation.
- **Process Bombing**: `--pids-limit=64` stops fork bombs with `BlockingIOError`.

### Layer 4: Network Isolation
Containers run with `--network none` by default. Socket calls immediately fail with `OSError: Network is unreachable`.

### Layer 5: Output Stream Truncation
Stdout and stderr are capped at `MAX_OUTPUT_SIZE_BYTES` (512 KB), preventing memory exhaustion from infinite logging loops.

---

## 3. Fallback Isolated Runner Specification

> [!CAUTION]
> **Strict Execution Boundary Policy**:
> Untrusted code is never executed directly on the host in production. The `FallbackIsolatedRunner` is explicitly gated under `ALLOW_LOCAL_FALLBACK_FOR_TESTING=True` solely for offline CI unit tests and synthetic dry-runs. In production environments where Docker is unavailable, the system halts with `EXECUTION_SANDBOX_UNAVAILABLE`.
