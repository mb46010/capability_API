# BUG-008: Potential Race Condition in Idempotency Cache

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/client.py`
- **Line(s)**: 74-83, 139-172

## Issue Description
The idempotency cache in the Workday simulator is not thread-safe. When running with multiple workers (as in production with `workers=4`), concurrent requests with the same idempotency key can race:

```python
# ❌ RACE CONDITION - Non-atomic check-then-act
if idempotency_key and is_write:
    cached_result = self._get_cached(idempotency_key)  # Check
    if cached_result is not None:
        return cached_result
    # WINDOW: Another request can reach here simultaneously

# ... execute operation ...

if idempotency_key and is_write:
    self._set_cached(idempotency_key, result)  # Set
```

Two concurrent requests with the same idempotency key can both pass the check and execute the operation, defeating the purpose of idempotency.

## Impact
- **Duplicate operations**: Same write operation executed multiple times
- **Data corruption**: Potential for inconsistent state in HR data
- **Idempotency guarantee broken**: Clients relying on idempotency may see unexpected behavior

## Root Cause
The `OrderedDict` used for caching is not thread-safe. The check-then-act pattern between `_get_cached()` and `_set_cached()` is not atomic. Python's GIL does not protect against this type of race condition in async code with `await` points.

## How to Fix

### Code Changes
Use a thread-safe approach with locking:

```python
# ✅ FIXED - Thread-safe idempotency
import asyncio
from collections import OrderedDict
from typing import Dict, Any, Optional, Tuple

class WorkdaySimulator(ConnectorPort):
    def __init__(self, config: Optional[WorkdaySimulationConfig] = None):
        # ... existing init ...
        self._idempotency_lock = asyncio.Lock()
        self._idempotency_cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        idempotency_key = parameters.get("idempotency_key")
        is_write = any(kw in action for kw in ["update", "terminate", "request", "approve", "cancel"])

        if idempotency_key and is_write:
            async with self._idempotency_lock:
                cached_result = self._get_cached(idempotency_key)
                if cached_result is not None:
                    return cached_result

                # Execute while holding lock to prevent races
                result = await self._execute_action(action, parameters)
                self._set_cached(idempotency_key, result)
                return result

        return await self._execute_action(action, parameters)
```

### Steps
1. Add `asyncio.Lock()` for idempotency cache access
2. Wrap the check-get-execute-set sequence in an async context manager
3. Consider using a distributed cache (Redis) for multi-instance deployments
4. Add tests for concurrent idempotency key handling

## Verification

### Test Cases
1. Send 10 concurrent requests with same idempotency key - only 1 should execute
2. Verify idempotent response is returned for subsequent requests
3. Load test with high concurrency

### Verification Steps
1. Write a concurrent test using `asyncio.gather()`
2. Verify single execution in audit logs
3. Run stress test with multiple workers

## Related Issues
- None

---
*Discovered: 2026-02-03*
