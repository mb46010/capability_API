import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

class JSONLLogger:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # PII Patterns to redact
        self.pii_patterns = {
            "email": r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+',
            "phone": r'\+?1?\d{9,15}',
            "ssn": r'\d{3}-\d{2}-\d{4}',
            "salary": r'"amount"\s*:\s*\d+(\.\d+)?' 
        }

    def _redact(self, data: Any) -> Any:
        """
        Recursively redact PII from dictionaries and strings.
        """
        if isinstance(data, dict):
            return {k: self._redact(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._redact(item) for item in data]
        elif isinstance(data, str):
            redacted = data
            # Simple heuristic redaction
            # In a real system, we'd use named entity recognition or strict field whitelisting
            # Here we apply regex replacements for common patterns
            
            # Redact email (keep domain?) -> "REDACTED_EMAIL"
            redacted = re.sub(self.pii_patterns["email"], "[REDACTED_EMAIL]", redacted)
            
            # Redact phone
            redacted = re.sub(self.pii_patterns["phone"], "[REDACTED_PHONE]", redacted)
            
            return redacted
        return data

    def _redact_field_aware(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact specific sensitive fields by name.
        """
        sensitive_fields = ["personal_email", "phone", "base_salary", "bonus_target", "total_compensation"]
        
        cleaned = data.copy()
        for key, value in data.items():
            if key in sensitive_fields:
                cleaned[key] = "[REDACTED]"
            elif isinstance(value, dict):
                cleaned[key] = self._redact_field_aware(value)
            elif isinstance(value, list):
                cleaned[key] = [self._redact_field_aware(i) if isinstance(i, dict) else i for i in value]
        return cleaned

    def log_event(self, event_type: str, payload: Dict[str, Any], actor: str = "system"):
        """
        Log an event to the JSONL file with PII redaction.
        """
        # 1. Redact Payload
        safe_payload = self._redact_field_aware(payload)
        
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "actor": actor,
            "payload": safe_payload
        }
        
        # 2. Append to file
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
