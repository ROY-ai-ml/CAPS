"""Unit Tests for ErrorClassifier."""
from app.observation.classifier import ErrorClassifier
from app.schemas.enums import ErrorType


def test_classify_keyerror():
    stderr = """
Traceback (most recent call last):
  File "main.py", line 12, in <module>
    total = df["Total_Revenue_Amount"].sum()
  File "pandas/core/frame.py", line 3807, in __getitem__
    indexer = self.columns.get_loc(key)
KeyError: 'Total_Revenue_Amount'
"""
    err_type, err_msg, failing_line = ErrorClassifier.classify(exit_code=1, stderr=stderr)
    assert err_type == ErrorType.KEY_ERROR
    assert "KeyError" in err_msg
    assert failing_line == 'total = df["Total_Revenue_Amount"].sum()'


def test_classify_syntaxerror():
    stderr = """
  File "main.py", line 4
    print("Starting analysis"
                             ^
SyntaxError: '(' was never closed
"""
    err_type, err_msg, failing_line = ErrorClassifier.classify(exit_code=1, stderr=stderr)
    assert err_type == ErrorType.SYNTAX_ERROR
    assert "SyntaxError" in err_msg


def test_classify_timeout():
    err_type, err_msg, _ = ErrorClassifier.classify(exit_code=124, stderr="SandboxTimeout: Terminated after 30s")
    assert err_type == ErrorType.TIMEOUT


def test_classify_oom():
    err_type, err_msg, _ = ErrorClassifier.classify(exit_code=137, stderr="Killed", oom_killed=True)
    assert err_type == ErrorType.MEMORY_LIMIT


def test_classify_import_error():
    stderr = """
Traceback (most recent call last):
  File "main.py", line 1, in <module>
    import non_existent_package
ModuleNotFoundError: No module named 'non_existent_package'
"""
    err_type, err_msg, _ = ErrorClassifier.classify(exit_code=1, stderr=stderr)
    assert err_type == ErrorType.IMPORT_ERROR
