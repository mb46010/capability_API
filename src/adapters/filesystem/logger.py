import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class JSONDateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "isoformat"):
            return obj.isoformat()
        return super().default(obj)

class JSONLLogger:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # PII Patterns to redact
        self.pii_patterns = {
            "email": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            # Phone: Matches international +1-555... or local 555-555-5555 or (555) 555-5555
            "phone": r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
            # SSN: Matches 000-00-0000 or 000000000
            "ssn": r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',
            "salary": r'"amount"\s*:\s*\d+(\.\d+)?' 
        }

    def _redact(self, data: Any, key_name: Optional[str] = None) -> Any:
        """
        Recursively redact PII from dictionaries, lists, and strings.
        Combines field-name heuristics with pattern matching.
        """
        # 1. Field Name Heuristic (Redact value completely if key matches)
        sensitive_fields = ["personal_email", "phone", "mobile", "ssn", "base_salary", "bonus_target", "total_compensation", "password", "secret", "token"]
        if key_name and key_name.lower() in sensitive_fields:
            return "[REDACTED]"

        # 2. Recursion
        if isinstance(data, dict):
            return {k: self._redact(v, key_name=k) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact(item) for item in data]
        
        # 3. Pattern Matching (Fallback for strings in non-sensitive fields)
        elif isinstance(data, str):
            redacted = data
            for name, pattern in self.pii_patterns.items():
                replacement = f"[REDACTED_{name.upper()}]"
                redacted = re.sub(pattern, replacement, redacted)
            return redacted
            
        return data

    def log_event(self, event_type: str, payload: Dict[str, Any], actor: str = "system"):
        """
        Log an event to the JSONL file with robust PII redaction.
        """
        # 1. Redact Payload
        safe_payload = self._redact(payload)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "payload": safe_payload
        }
        
        # 2. Append to file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, cls=JSONDateTimeEncoder) + "\n")
