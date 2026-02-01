# BUG-008: MCP Token Cache Memory Leak

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/mcp/adapters/auth.py`
- **Line(s)**: 11, 86-121

## Issue Description
The MCP token cache stores exchanged tokens but only removes them when they're accessed after expiration, not proactively. Tokens that are never re-accessed remain in memory indefinitely:

```python
# Global cache - never cleaned up proactively
_mcp_token_cache: Dict[str, Tuple[str, float]] = {}

async def get_mcp_token(user_token: str) -> str:
    # Cache key based on token signature
    cache_key = token_parts[-1] if len(token_parts) == 3 else user_token

    now = time.time()
    if cache_key in _mcp_token_cache:
        cached_token, expires_at = _mcp_token_cache[cache_key]
        if now < expires_at:
            return cached_token
        else:
            del _mcp_token_cache[cache_key]  # Only cleaned if accessed!

    # ... exchange token ...

    # Cache for 4 minutes
    expires_at = now + 240
    _mcp_token_cache[cache_key] = (mcp_token, expires_at)

    return mcp_token
```

## Impact
- **Memory Growth**: Cache grows over time with tokens that are never re-accessed
- **Information Retention**: Old token signatures (cache keys) are retained longer than necessary
- **Resource Exhaustion**: Under high user load, cache can grow significantly

## Root Cause
The cache cleanup is lazy (only happens on access), so tokens from users who make one request and never return stay in memory forever. There's no background cleanup or maximum size limit.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Use TTLCache with automatic expiration and size limit
from cachetools import TTLCache
import threading

# Cache with max 5000 entries and 5 minute TTL (matches token lifetime)
_mcp_token_cache: TTLCache = TTLCache(maxsize=5000, ttl=300)
_cache_lock = threading.Lock()

async def get_mcp_token(user_token: str) -> str:
    token_parts = user_token.split(".")
    cache_key = token_parts[-1] if len(token_parts) == 3 else user_token

    # Thread-safe cache access
    with _cache_lock:
        cached_token = _mcp_token_cache.get(cache_key)
        if cached_token:
            logger.debug("Returning cached MCP token")
            return cached_token

    # Exchange token (outside lock to avoid blocking)
    logger.info("Exchanging user token for MCP scope")
    # ... exchange logic ...

    with _cache_lock:
        _mcp_token_cache[cache_key] = mcp_token

    return mcp_token
```

### Alternative: Add periodic cleanup
```python
# ✅ FIXED: Manual cleanup with periodic timer
import asyncio

_cleanup_task: Optional[asyncio.Task] = None

async def _periodic_cache_cleanup():
    """Background task to clean expired entries every 5 minutes."""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        now = time.time()
        expired_keys = [
            k for k, (_, exp) in _mcp_token_cache.items()
            if now >= exp
        ]
        for k in expired_keys:
            _mcp_token_cache.pop(k, None)
        if expired_keys:
            logger.debug(f"Cleaned {len(expired_keys)} expired MCP tokens from cache")

def start_cache_cleanup():
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(_periodic_cache_cleanup())
```

### Steps
1. Replace the plain dict with TTLCache or implement periodic cleanup
2. Add max size limit to prevent unbounded growth
3. Ensure thread safety if using async/multi-threaded access
4. Add monitoring for cache statistics

## Verification

### Test Cases
1. Cache size should not exceed maximum after many unique users
2. Expired entries should be automatically removed
3. Cache hits should still work for active tokens
4. No memory growth under sustained load

### Verification Steps
```python
# Test cache doesn't grow unbounded
async def test_mcp_cache_bounded():
    for i in range(10000):
        fake_token = f"header.payload.signature{i}"
        # Simulate token exchange
        _mcp_token_cache[f"signature{i}"] = (f"mcp_token_{i}", time.time() + 240)

    assert len(_mcp_token_cache) <= 5000  # Max size enforced
```

## Related Issues
- Similar to BUG-007 (idempotency cache)

---
*Discovered: 2026-02-01*
