# BUG-012: Potential Path Traversal in Audit Log Path

## Severity
🟢 LOW

## Location
- **File(s)**: `src/adapters/filesystem/logger.py`
- **Line(s)**: 15-17

## Issue Description
The `JSONLLogger` accepts a `log_path` parameter that's used directly to create files. While the default is safe, if this is ever made configurable via environment variable or user input, it could allow path traversal:

```python
class JSONLLogger:
    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path)  # No validation
        self.log_path.parent.mkdir(parents=True, exist_ok=True)  # Creates arbitrary directories
```

If `log_path` were set to `../../../../etc/cron.d/malicious`, this could write files to sensitive locations.

## Impact
- **Low Risk Currently**: The path is hardcoded and not user-controllable
- **Future Risk**: If made configurable, could allow arbitrary file writes
- **Information Disclosure**: Could write logs to accessible locations

## Root Cause
The path is not validated or sanitized before use. While currently safe due to hardcoding, this is a defense-in-depth issue.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Validate log path is within expected directory
import os

class JSONLLogger:
    ALLOWED_LOG_DIR = Path("logs").resolve()

    def __init__(self, log_path: str = "logs/audit.jsonl"):
        self.log_path = Path(log_path).resolve()

        # Validate path is within allowed directory
        try:
            self.log_path.relative_to(self.ALLOWED_LOG_DIR)
        except ValueError:
            raise ValueError(f"Log path must be within {self.ALLOWED_LOG_DIR}")

        self.log_path.parent.mkdir(parents=True, exist_ok=True)
```

### Alternative: Use absolute path from config
```python
# ✅ FIXED: Use validated config path
from src.lib.config_validator import settings

class JSONLLogger:
    def __init__(self):
        # Path comes from validated settings, not user input
        self.log_path = Path(settings.AUDIT_LOG_PATH).resolve()
        if not str(self.log_path).startswith(str(Path.cwd())):
            raise ValueError("Audit log path must be within project directory")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
```

### Steps
1. Add path validation to ensure log files stay within expected directory
2. If making configurable, add validation in settings
3. Consider using absolute paths in configuration

## Verification

### Test Cases
1. Default path - should work normally
2. Path traversal attempt (`../../../etc/passwd`) - should raise ValueError
3. Valid relative path within logs/ - should work

### Verification Steps
```python
# Test path traversal prevention
def test_logger_path_traversal():
    with pytest.raises(ValueError):
        JSONLLogger("../../../etc/cron.d/malicious")

    with pytest.raises(ValueError):
        JSONLLogger("/etc/passwd")

    # Should work
    logger = JSONLLogger("logs/audit.jsonl")
    logger = JSONLLogger("logs/subdirectory/audit.jsonl")
```

## Related Issues
- None

---
*Discovered: 2026-02-01*
