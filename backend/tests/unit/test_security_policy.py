"""Unit Tests for SecurityPolicyEngine."""
from app.schemas.enums import NetworkPolicy
from app.security.policy import SecurityPolicyEngine


def test_clean_data_science_code_allowed():
    code = """
import pandas as pd
import matplotlib.pyplot as plt

df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
plt.plot(df["x"], df["y"])
plt.savefig("plot.png")
"""
    engine = SecurityPolicyEngine()
    report = engine.inspect_code(code)
    assert report.allowed is True
    assert report.risk_level == "low"
    assert len(report.violations) == 0


def test_subprocess_blocked():
    code = """
import subprocess
subprocess.run(["rm", "-rf", "/"])
"""
    engine = SecurityPolicyEngine()
    report = engine.inspect_code(code)
    assert report.allowed is False
    assert report.risk_level == "high"
    assert any("subprocess" in v for v in report.violations)


def test_eval_exec_blocked():
    code = """
command = "print('pwned')"
eval(command)
exec(command)
"""
    engine = SecurityPolicyEngine()
    report = engine.inspect_code(code)
    assert report.allowed is False
    assert any("eval" in v for v in report.violations)
    assert any("exec" in v for v in report.violations)


def test_path_traversal_blocked():
    code = """
with open("../../etc/passwd", "r") as f:
    data = f.read()
"""
    engine = SecurityPolicyEngine()
    report = engine.inspect_code(code)
    assert report.allowed is False
    assert any("path traversal" in v for v in report.violations)


def test_network_import_blocked_when_disabled():
    code = """
import requests
resp = requests.get("https://malicious.com")
"""
    engine = SecurityPolicyEngine(network_policy=NetworkPolicy.DISABLED)
    report = engine.inspect_code(code)
    assert report.allowed is False
    assert any("Network call" in v for v in report.violations)
