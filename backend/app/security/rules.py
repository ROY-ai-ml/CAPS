"""Forbidden Modules, Functions, and Path Patterns for AST Policy Engine."""

FORBIDDEN_MODULES = {
    "subprocess",
    "os.system",
    "pty",
    "posix_spawn",
    "commands",
    "winreg",
    "ctypes",
    "multiprocessing.spawn",
    "importlib",
    "pip",
    "venv",
}

SUSPICIOUS_CALLS = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
    "os.remove",
    "os.unlink",
    "os.rmdir",
    "shutil.rmtree",
    "os.system",
    "os.popen",
    "os.kill",
    "os.fork",
}

FORBIDDEN_PATHS = [
    "..",
    "/etc",
    "/var",
    "/root",
    "/usr",
    "/bin",
    "/sbin",
    "/proc",
    "/sys",
    "C:\\Windows",
    "C:\\Program Files",
    "C:\\Users",
]
