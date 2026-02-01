import logging
import re
from typing import Pattern, List, Tuple
from src.lib.context import request_id_ctx

class PIIMaskingFormatter(logging.Formatter):
    """
    Formatter that masks PII patterns in log messages.
    """
    
    # Pre-compile regex patterns
    PATTERNS: List[Tuple[Pattern, str]] = [
        # Email
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), '[EMAIL]'),
        # SSN (Simple)
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), '[SSN]'),
        # Phone (US-ish)
        (re.compile(r'\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b'), '[PHONE]'),
    ]

    def format(self, record):
        original_msg = super().format(record)
        masked_msg = original_msg
        
        for pattern, replacement in self.PATTERNS:
            masked_msg = pattern.sub(replacement, masked_msg)
            
        # Prepend Request ID if available
        rid = request_id_ctx.get()
        if rid:
            return f"[{rid}] {masked_msg}"
            
        return masked_msg

def setup_logging(level=logging.INFO):
    handler = logging.StreamHandler()
    handler.setFormatter(PIIMaskingFormatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
    
    logger = logging.getLogger()
    logger.setLevel(level)
    # Remove existing handlers to avoid duplicates
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.addHandler(handler)

def log_provenance(action: str, resource: str, effect: str, reason: str = None, **metadata):
    """
    Structured provenance log entry for security events.
    """
    msg = f"PROVENANCE: {action} on {resource} -> {effect}"
    if reason:
        msg += f" (Reason: {reason})"
    if metadata:
        msg += f" | Metadata: {metadata}"
    
    logging.info(msg)

