import pytest
import logging
from src.lib.logging import PIIMaskingFormatter

class LogRecord:
    def __init__(self, msg):
        self.msg = msg
        self.args = None
        self.exc_info = None
        self.exc_text = None
        self.stack_info = None

def test_pii_masking_email():
    formatter = PIIMaskingFormatter()
    # Simple log record mock
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg="User email is john.doe@example.com", args=None, exc_info=None
    )
    formatted = formatter.format(record)
    assert "john.doe@example.com" not in formatted
    assert "[EMAIL]" in formatted

def test_pii_masking_phone():
    formatter = PIIMaskingFormatter()
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg="Call +1-555-012-3456 for help", args=None, exc_info=None
    )
    formatted = formatter.format(record)
    assert "+1-555-012-3456" not in formatted
    assert "[PHONE]" in formatted

def test_pii_masking_json_structure():
    formatter = PIIMaskingFormatter()
    json_msg = '{"email": "jane@test.com", "id": 123}'
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="test.py", lineno=1,
        msg=json_msg, args=None, exc_info=None
    )
    formatted = formatter.format(record)
    assert "jane@test.com" not in formatted
    assert "[EMAIL]" in formatted
