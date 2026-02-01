# 001: Add Request Timeout Middleware

## Impact
**Effort**: Low (2 hours) | **Impact**: High | **Priority**: 1

## Location
- **File(s)**: `src/main.py`
- **Component/Module**: FastAPI Application Middleware

## Current State

The API has no request-level timeout enforcement. Long-running requests (e.g., slow connector calls, complex org chart traversals) can tie up worker threads indefinitely:

```python
# No timeout protection
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # ... no timeout wrapper
    response = await call_next(request)  # Can hang forever
```

The connector has latency simulation but no hard timeout at the HTTP layer.

## Proposed Improvement

Add timeout middleware that cancels requests exceeding a configurable threshold (e.g., 30 seconds). This protects against:
- Slow external dependencies
- Runaway recursive operations
- Resource exhaustion from accumulated hanging requests

## Benefits

- **Reliability**: Prevents worker thread exhaustion from stuck requests
- **User Experience**: Fast failure is better than infinite waiting
- **Resource Management**: Frees resources predictably
- **Observability**: Clear timeout errors are easier to debug than connection resets

**Estimated impact**: Prevents potential DoS from slow operations

## Implementation

### Approach
Add an `asyncio.timeout()` wrapper in middleware. Return 504 Gateway Timeout when exceeded.

### Estimated Effort
2 hours (including testing)

### Steps
1. Add timeout setting to `AppSettings`
2. Create timeout middleware
3. Add to middleware chain (before request ID)
4. Add tests for timeout behavior

## Example

### Before
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    response = await call_next(request)  # No timeout
    response.headers["X-Request-ID"] = request_id
    return response
```

### After
```python
import asyncio
from starlette.responses import JSONResponse

REQUEST_TIMEOUT_SECONDS = 30

@app.middleware("http")
async def add_timeout(request: Request, call_next):
    try:
        async with asyncio.timeout(REQUEST_TIMEOUT_SECONDS):
            return await call_next(request)
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content={
                "error_code": "GATEWAY_TIMEOUT",
                "message": "Request timed out",
            }
        )

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    # ... existing code
```

## Considerations

- Timeout should be configurable per environment (longer for dev)
- Consider endpoint-specific timeouts for known slow operations
- Ensure cleanup happens properly on timeout (no resource leaks)
- Log timeout events for monitoring

## Related Improvements
- 003-add-structured-request-logging.md (log timeout events)

---
*Identified: 2026-02-01*
