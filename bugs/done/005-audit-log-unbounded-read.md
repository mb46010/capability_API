# BUG-005: Audit Log Endpoint Reads Entire Log File into Memory

## Severity
🟡 MEDIUM

## Location
- **File(s)**: src/api/routes/audit.py
- **Line(s)**: src/api/routes/audit.py:28-35

## Issue Description
`/audit/recent` reads the entire audit log into memory with `readlines()` and then slices the last `limit` entries. Large audit files can cause high memory usage and slow responses, especially if `limit` is large or the log grows unbounded.

**Current behavior:**
```python
# ❌ VULNERABLE
lines = f.readlines()
for line in lines[-limit:]:
    if line.strip():
        logs.append(json.loads(line))
```

## Impact
- Potential memory spikes or OOM errors on large log files.
- Slow responses for administrators and degraded API performance.
- DoS risk if the log file is large and `limit` is unbounded.

## Root Cause
The implementation reads the full file into memory instead of streaming or tailing.

## How to Fix

### Code Changes
Stream the file using a fixed-size deque or seek from the end, and enforce a maximum `limit`.

```python
# ✅ FIXED (example)
from collections import deque

max_limit = min(limit, 200)
with open(DEFAULT_LOG_PATH, "r", encoding="utf-8") as f:
    tail = deque(f, maxlen=max_limit)

for line in tail:
    if line.strip():
        logs.append(json.loads(line))
```

### Steps
1. Clamp `limit` to a safe maximum.
2. Use `deque` or a tailing strategy to avoid loading full files.
3. Add a test for large audit logs and a large `limit` value.

## Verification

### Test Cases
- Large log file (e.g., 100k lines) with `limit=20` returns quickly and uses minimal memory.
- `limit` above max is clamped to max.

### Verification Steps
1. Generate a large audit log file.
2. Call `/audit/recent?limit=2000` and confirm it clamps and returns quickly.
3. Monitor memory usage during the request to ensure it does not spike.

## Related Issues
- None.

---
*Discovered: 2026-02-02T22:06:45Z*
