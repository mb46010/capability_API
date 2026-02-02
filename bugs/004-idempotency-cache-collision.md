# BUG-004: Idempotency Cache Key Not Scoped to Action or Principal

## Severity
🟡 MEDIUM

## Location
- **File(s)**: src/adapters/workday/client.py
- **Line(s)**: src/adapters/workday/client.py:74-132, 139-162

## Issue Description
The idempotency cache uses only the raw `idempotency_key` as its cache key. If two different actions or principals reuse the same key, the cached result from the first request is returned for the second request. This can cause incorrect behavior and cross-request data leakage.

**Current behavior:**
```python
# ❌ VULNERABLE
cached_result = self._get_cached(idempotency_key)
...
self._set_cached(idempotency_key, result)
```

## Impact
- Incorrect responses for legitimate requests that reuse an idempotency key across different actions.
- Potential leakage of another principal’s action result if they reused the same key.
- Breaks idempotency semantics (should be scoped per action/principal).

## Root Cause
The cache key is not scoped to the action and principal context; it only uses the raw idempotency key.

## How to Fix

### Code Changes
Scope the cache key to both the action and principal (and optionally domain) to avoid collisions.

```python
# ✅ FIXED (example)
principal_id = parameters.get("principal_id", "unknown")
cache_key = f"{principal_id}:{action}:{idempotency_key}"

cached_result = self._get_cached(cache_key)
...
self._set_cached(cache_key, result)
```

### Steps
1. Compute a composite cache key using `principal_id` and `action`.
2. Update `_get_cached` and `_set_cached` callers to use the composite key.
3. Add tests for idempotency collisions across different actions and principals.

## Verification

### Test Cases
- Two different actions with the same idempotency key should not share results.
- Two different principals with the same idempotency key should not share results.

### Verification Steps
1. Call `update_contact_info` with `idempotency_key=K`, record response.
2. Call `terminate_employee` with the same key and a different principal.
3. Confirm the second response is not the first action’s cached payload.

## Related Issues
- None.

---
*Discovered: 2026-02-02T22:06:45Z*
