# BUG-004: Time-window policies fail for overnight ranges

## Severity
🟡 MEDIUM

## Location
- **File(s)**: src/domain/services/policy_engine.py
- **Line(s)**: 207-227

## Issue Description
The time-window condition enforces `start_time <= current_time <= end_time`. This fails for overnight ranges such as 22:00–06:00 where `start_time > end_time`. In those cases, all requests during the intended window are denied.

## Impact
- Policies meant to allow access overnight never match.
- Users/services relying on overnight access windows are blocked unexpectedly.

## Root Cause
Time window logic does not handle ranges that cross midnight.

## How to Fix

### Code Changes
- Handle the overnight case by allowing times that are >= start OR <= end when `start_time > end_time`.

Example direction:
```python
if start_time <= end_time:
    allowed = start_time <= current_time <= end_time
else:
    # crosses midnight
    allowed = current_time >= start_time or current_time <= end_time
if not allowed:
    return False
```

### Steps
1. Update `_evaluate_conditions` time-window logic.
2. Add unit tests for same-day and overnight windows.

## Verification

### Test Cases
- Window 09:00–17:00 allows 10:00, denies 20:00.
- Window 22:00–06:00 allows 23:00 and 02:00, denies 12:00.

### Verification Steps
1. Add tests for both window types.
2. Run `pytest tests/unit/test_policy_engine.py`.

## Related Issues
None.

---
*Discovered: 2026-02-01*
