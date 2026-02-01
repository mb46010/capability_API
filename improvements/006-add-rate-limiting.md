# 006: Add Rate Limiting to API Endpoints

## Impact
**Effort**: Medium (3-4 hours) | **Impact**: High | **Priority**: 3

## Location
- **File(s)**: `src/main.py`, `src/lib/rate_limiter.py` (new)
- **Component/Module**: API Security Layer

## Current State

No rate limiting is implemented. The policy file defines rate limits but they're not enforced:

```yaml
# config/policy-workday.yaml
connector_constraints:
  workday:
    rate_limit:
      requests_per_minute: 100
      burst: 20
    # ... not enforced anywhere
```

Any authenticated client can send unlimited requests, enabling:
- Resource exhaustion attacks
- Abuse of expensive operations (org chart traversal)
- Denial of service to other users

## Proposed Improvement

Implement token-bucket rate limiting at the API layer, respecting the policy-defined limits. Rate limit per principal (subject claim).

## Benefits

- **Security**: Prevents abuse and DoS attacks
- **Fairness**: Ensures no single client monopolizes resources
- **Cost Control**: Limits expensive backend calls
- **Compliance**: Many security frameworks require rate limiting

**Estimated protection**: Prevents 99% of abuse scenarios

## Implementation

### Approach
Use an in-memory rate limiter (token bucket algorithm) keyed by principal ID. Return 429 when exceeded.

### Estimated Effort
3-4 hours

### Steps
1. Create `src/lib/rate_limiter.py` with token bucket implementation
2. Add rate limit middleware or dependency
3. Load limits from policy config
4. Return proper 429 response with Retry-After header
5. Add tests

## Example

### Before
```python
# No rate limiting - unlimited requests allowed
@router.post("/{domain}/{action}")
async def execute_action(...):
    # Directly processes request
```

### After
```python
# src/lib/rate_limiter.py
import time
from collections import defaultdict
from dataclasses import dataclass

@dataclass
class RateLimitConfig:
    requests_per_minute: int = 100
    burst: int = 20

class TokenBucket:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()

    def consume(self, tokens: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
        self.last_update = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def retry_after(self) -> int:
        """Seconds until a token is available."""
        if self.tokens >= 1:
            return 0
        return int((1 - self.tokens) / self.rate) + 1

class RateLimiter:
    def __init__(self, config: RateLimitConfig):
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(
                rate=config.requests_per_minute / 60,
                capacity=config.burst
            )
        )

    def check(self, key: str) -> tuple[bool, int]:
        """Returns (allowed, retry_after_seconds)."""
        bucket = self.buckets[key]
        allowed = bucket.consume()
        return allowed, bucket.retry_after
```

```python
# src/main.py
from src.lib.rate_limiter import RateLimiter, RateLimitConfig

rate_limiter = RateLimiter(RateLimitConfig())

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Skip health check
    if request.url.path == "/health":
        return await call_next(request)

    # Extract principal from token (if available)
    auth_header = request.headers.get("Authorization", "")
    principal_key = "anonymous"
    if auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            claims = jwt.decode(token, options={"verify_signature": False})
            principal_key = claims.get("sub", "anonymous")
        except:
            pass

    allowed, retry_after = rate_limiter.check(principal_key)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={
                "error_code": "RATE_LIMITED",
                "message": "Too many requests",
                "retry_after": retry_after
            },
            headers={"Retry-After": str(retry_after)}
        )

    return await call_next(request)
```

## Considerations

- In-memory limiter resets on restart (OK for single-instance)
- For multi-instance, use Redis-based limiter
- Consider different limits for different endpoint classes
- Exempt internal/admin endpoints if needed
- Log rate limit events for monitoring

## Related Improvements
- 001-add-request-timeout-middleware.md
- 003-add-structured-request-logging.md

---
*Identified: 2026-02-01*
