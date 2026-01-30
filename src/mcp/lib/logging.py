import logging
import re
import json
from typing import Any
from src.mcp.lib.config import settings
import os

class PIIMaskingFilter(logging.Filter):
    """
    Filter to mask PII in log records.
    """
    MASK = "***"
    # Basic patterns for email, phone, and potential SSN/Tax IDs
    PATTERNS = [
        (re.compile(r'[\w\.-]+@[\w\.-]+\.\w+'), MASK), # Email
        (re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'), MASK), # Phone
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), MASK), # SSN
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self._mask_text(record.msg)
        elif isinstance(record.msg, dict):
            record.msg = self._mask_dict(record.msg)
        
        if hasattr(record, 'args') and record.args:
            if isinstance(record.args, dict):
                record.args = self._mask_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(self._mask_text(str(arg)) if isinstance(arg, str) else arg for arg in record.args)

        return True

    def _mask_text(self, text: str) -> str:
        for pattern, mask in self.PATTERNS:
            text = pattern.sub(mask, text)
        return text

    def _mask_dict(self, data: dict) -> dict:
        masked = {}
        for k, v in data.items():
            # Sensitive field names
            if any(sensitive in k.lower() for sensitive in ["email", "phone", "ssn", "salary", "compensation", "address"]):
                masked[k] = self.MASK
            elif isinstance(v, dict):
                masked[k] = self._mask_dict(v)
            elif isinstance(v, list):
                masked[k] = [self._mask_dict(i) if isinstance(i, dict) else i for i in v]
            elif isinstance(v, str):
                masked[k] = self._mask_text(v)
            else:
                masked[k] = v
        return masked

def setup_logging():
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Ensure log directory exists
    log_dir = os.path.dirname(settings.AUDIT_LOG_PATH)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger()
    pii_filter = PIIMaskingFilter()
    logger.addFilter(pii_filter)
    
    return logger

class JSONLAuditLogger:
    def __init__(self, path: str = settings.AUDIT_LOG_PATH):
        self.path = path
        self.masker = PIIMaskingFilter()

    def log(self, event_type: str, payload: dict, principal_id: str, status: str = "success"):
        # Ensure dir exists
        log_dir = os.path.dirname(self.path)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        entry = {
            "timestamp": logging.Formatter().formatTime(logging.LogRecord("", 0, "", 0, "", None, None), "%Y-%m-%dT%H:%M:%SZ"),
            "event_type": event_type,
            "principal_id": principal_id,
            "status": status,
            "payload": self.masker._mask_dict(payload)
        }
        
        with open(self.path, "a") as f:
            f.write(json.dumps(entry) + "\n")

audit_logger = JSONLAuditLogger()
