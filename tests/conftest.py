import pytest
import os
import shutil
from src.adapters.filesystem.logger import JSONLLogger

@pytest.fixture
def test_logger(tmp_path):
    """
    Fixture providing a JSONLLogger instance pointing to a temporary file.
    """
    log_dir = tmp_path / "logs"
    log_file = log_dir / "audit.jsonl"
    return JSONLLogger(log_path=str(log_file))
