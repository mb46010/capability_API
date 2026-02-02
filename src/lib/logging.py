import logging
import json
import sys
import re
from datetime import datetime, timezone
from typing import Any, Pattern, List, Tuple
from src.lib.context import get_request_id

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging with PII masking.
    """
    
    # Pre-compile regex patterns for PII masking
    PATTERNS: List[Tuple[Pattern, str]] = [
        # Email
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), '[EMAIL]'),
        # SSN (Simple)
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
        # Phone (US-ish)
        (re.compile(r'\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b'), '[PHONE]'),
    ]

    def _mask_pii(self, text: str) -> str:
        if not isinstance(text, str):
            return text
        for pattern, replacement in self.PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def _mask_object(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {k: self._mask_object(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._mask_object(i) for i in obj]
        elif isinstance(obj, str):
            return self._mask_pii(obj)
        return obj

    def format(self, record: logging.LogRecord) -> str:
        # Mask the main message
        message = self._mask_pii(record.getMessage())

        # Basic log object
        log_obj: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": message,
        }

        # Add request_id from context if available
        request_id = get_request_id()
        if request_id:
            log_obj["request_id"] = request_id

        # Add extra data if present, and mask it
        if hasattr(record, "extra_data"):
            masked_extra = self._mask_object(record.extra_data)
            log_obj.update(masked_extra)
        
        # Add exception info if present
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)

class PIIMaskingFormatter(StructuredFormatter):
    """
    Compatibility class for existing tests that expect PIIMaskingFormatter.
    This now produces JSON instead of plain text, but still masks PII.
    If we strictly need plain text for compatibility, we might need to adjust.
    But usually, upgrading to structured logging means changing the format.
    """
    pass

def setup_logging(level: int = logging.INFO):
    """
    Configures the root logger to use structured JSON logging.
    """
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    
    root_logger = logging.getLogger()
    
    # Remove existing handlers to avoid duplicate logs
    for h in root_logger.handlers[:]:
        root_logger.removeHandler(h)
        
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Specific configuration for API request logger if needed
    logging.getLogger("api.requests").propagate = True

def log_provenance(action: str, resource: str, effect: str, reason: str = None, **metadata):
    """
    Structured provenance log entry for security events.
    """
    extra_data = {
        "action": action,
        "resource": resource,
        "effect": effect,
    }
    if reason:
        extra_data["reason"] = reason
    if metadata:
        extra_data.update(metadata)
    
    logging.info(
        f"PROVENANCE: {action} on {resource} -> {effect}",
        extra={"extra_data": extra_data}
    )