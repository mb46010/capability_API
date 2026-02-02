# BUG-006: Audit Log Endpoint Ignores Configured Audit Log Path

## Severity
🟢 LOW

## Location
- **File(s)**: src/api/routes/audit.py
- **Line(s)**: src/api/routes/audit.py:10-12, 21-31

## Issue Description
`/audit/recent` uses a hard-coded `DEFAULT_LOG_PATH` instead of the configured `AUDIT_LOG_PATH` from settings. If the audit logger writes to a non-default location, the endpoint will show "Log file not found" even though logs exist.

**Current behavior:**
```python
# ❌ VULNERABLE
DEFAULT_LOG_PATH = Path("logs/audit.jsonl")
...
with open(DEFAULT_LOG_PATH, "r", encoding="utf-8") as f:
    lines = f.readlines()
```

## Impact
- Admins cannot view audit logs when a custom log path is configured.
- Operational confusion during incident response or compliance reviews.

## Root Cause
The endpoint is not wired to the same configuration used by the audit logger.

## How to Fix

### Code Changes
Use the configured audit log path from settings.

```python
# ✅ FIXED (example)
from src.lib.config_validator import settings

AUDIT_LOG_PATH = Path(settings.AUDIT_LOG_PATH)
...
with open(AUDIT_LOG_PATH, "r", encoding="utf-8") as f:
    ...
```

### Steps
1. Import `settings` in `audit.py`.
2. Replace `DEFAULT_LOG_PATH` with `Path(settings.AUDIT_LOG_PATH)`.
3. Add a test that sets `AUDIT_LOG_PATH` and verifies `/audit/recent` returns entries.

## Verification

### Test Cases
- Set `AUDIT_LOG_PATH` to a non-default path and confirm `/audit/recent` reads it.

### Verification Steps
1. Configure `AUDIT_LOG_PATH=/tmp/audit.jsonl`.
2. Generate a log entry.
3. Call `/audit/recent` and confirm the entry is returned.

## Related Issues
- None.

---
*Discovered: 2026-02-02T22:06:45Z*
