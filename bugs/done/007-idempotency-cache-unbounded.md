# BUG-007: Unbounded Idempotency Cache Memory Leak

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/client.py`
- **Line(s)**: 40, 77-80, 129-130

## Issue Description
The WorkdaySimulator maintains an idempotency cache that grows indefinitely without any eviction policy:

```python
class WorkdaySimulator(ConnectorPort):
    def __init__(self, ...):
        # Idempotency cache (mapping idempotency_key to previous result)
        self._idempotency_cache: Dict[str, Dict[str, Any]] = {}

    async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        idempotency_key = parameters.get("idempotency_key")

        # Check cache
        if idempotency_key and is_write:
            if idempotency_key in self._idempotency_cache:
                return self._idempotency_cache[idempotency_key]  # Return cached

        # ... execute operation ...

        # Store in cache - NEVER EVICTED
        if idempotency_key and is_write:
            self._idempotency_cache[idempotency_key] = result
```

## Impact
- **Memory Exhaustion**: Over time, the cache grows unbounded leading to OOM conditions
- **Denial of Service**: An attacker can intentionally flood the system with unique idempotency keys
- **Performance Degradation**: Large cache causes dictionary lookup slowdowns

## Root Cause
The idempotency cache was implemented for correctness (ensuring write operations are idempotent) but lacks:
1. Maximum size limit
2. TTL-based expiration
3. LRU eviction policy

## How to Fix

### Code Changes

**Option A: Use TTL-based cache with max size**
```python
# ✅ FIXED: Add TTL and max size to idempotency cache
from collections import OrderedDict
import time

class WorkdaySimulator(ConnectorPort):
    IDEMPOTENCY_CACHE_MAX_SIZE = 10000
    IDEMPOTENCY_CACHE_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, ...):
        self._idempotency_cache: OrderedDict[str, tuple[Dict[str, Any], float]] = OrderedDict()

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached result if exists and not expired."""
        if key not in self._idempotency_cache:
            return None

        result, timestamp = self._idempotency_cache[key]
        if time.time() - timestamp > self.IDEMPOTENCY_CACHE_TTL_SECONDS:
            del self._idempotency_cache[key]
            return None

        # Move to end (LRU)
        self._idempotency_cache.move_to_end(key)
        return result

    def _set_cached(self, key: str, result: Dict[str, Any]):
        """Cache result with timestamp, evicting oldest if at capacity."""
        # Evict expired entries periodically
        self._cleanup_expired()

        # Evict oldest if at capacity
        while len(self._idempotency_cache) >= self.IDEMPOTENCY_CACHE_MAX_SIZE:
            self._idempotency_cache.popitem(last=False)

        self._idempotency_cache[key] = (result, time.time())

    def _cleanup_expired(self):
        """Remove expired entries."""
        now = time.time()
        expired = [
            k for k, (_, ts) in self._idempotency_cache.items()
            if now - ts > self.IDEMPOTENCY_CACHE_TTL_SECONDS
        ]
        for k in expired:
            del self._idempotency_cache[k]
```

**Option B: Use functools.lru_cache or cachetools**
```python
# ✅ FIXED: Use cachetools TTLCache
from cachetools import TTLCache

class WorkdaySimulator(ConnectorPort):
    def __init__(self, ...):
        # TTLCache with max 10000 entries, 1 hour TTL
        self._idempotency_cache = TTLCache(maxsize=10000, ttl=3600)
```

### Steps
1. Add TTL and max size to idempotency cache
2. Implement cleanup logic (either manual or via library)
3. Consider making cache parameters configurable
4. Add monitoring/metrics for cache size and hit rate

## Verification

### Test Cases
1. Add more than max_size entries - oldest should be evicted
2. Wait for TTL to expire - entries should be removed
3. Verify idempotency still works for recent operations
4. Load test with many unique keys - memory should remain bounded

### Verification Steps
```python
# Unit test for cache eviction
def test_idempotency_cache_eviction():
    simulator = WorkdaySimulator()

    # Fill cache beyond max size
    for i in range(15000):
        simulator._set_cached(f"key-{i}", {"result": i})

    # Should not exceed max size
    assert len(simulator._idempotency_cache) <= 10000

    # Oldest entries should be evicted
    assert "key-0" not in simulator._idempotency_cache
```

## Related Issues
- None

---
*Discovered: 2026-02-01*
