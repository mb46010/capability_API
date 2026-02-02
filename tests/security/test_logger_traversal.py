import pytest
import os
from pathlib import Path
from src.adapters.filesystem.logger import JSONLLogger

def test_logger_path_traversal_prevention():
    """Verify that JSONLLogger prevents path traversal."""
    
    # 1. Attempt to write to a sensitive system path
    with pytest.raises(ValueError) as excinfo:
        JSONLLogger(log_path="/etc/passwd")
    assert "Security Error: Log path escape detected" in str(excinfo.value)

    # 2. Attempt to write using traversal dots
    with pytest.raises(ValueError) as excinfo:
        JSONLLogger(log_path="../../../../../etc/shadow")
    assert "Security Error: Log path escape detected" in str(excinfo.value)

    # 3. Valid path within project root (should work)
    # Using a relative path that resolves inside project root
    logger = JSONLLogger(log_path="logs/test_audit.jsonl")
    assert "logs/test_audit.jsonl" in str(logger.log_path)
    
    # Cleanup if file was created
    if logger.log_path.exists():
        logger.log_path.unlink()

def test_logger_allows_temp_dir(tmp_path):
    """Verify that JSONLLogger allows paths within the temporary directory (needed for tests)."""
    log_file = tmp_path / "audit.jsonl"
    logger = JSONLLogger(log_path=str(log_file))
    assert logger.log_path == log_file.resolve()
    
    logger.log_event("test", {"foo": "bar"})
    assert log_file.exists()
