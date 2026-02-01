# 001: Add security headers middleware

## Impact
**Effort**: Low (1-2 hours) | **Impact**: High | **Priority**: 1

## Location
- **File(s)**: src/main.py
- **Component/Module**: FastAPI app middleware

## Current State
Responses do not consistently include baseline security headers. This leaves the API without common protections like clickjacking prevention and MIME sniffing defense.

## Proposed Improvement
Add a lightweight middleware to attach standard security headers to every response. Gate HSTS to non-local environments.

## Benefits
- Improves security posture with minimal code.
- Reduces risk of clickjacking and content-type sniffing issues.
- Aligns with common API hardening checklists.

## Implementation

### Approach
Add a simple `@app.middleware("http")` block to append headers after `call_next`.

### Estimated Effort
1-2 hours (including quick verification).

### Steps
1. Add a security-headers middleware in `src/main.py`.
2. Set `Strict-Transport-Security` only when `settings.ENVIRONMENT != "local"`.
3. Verify headers appear in a sample response.

## Example

### Before
```python
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response
```

### After
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    if settings.ENVIRONMENT != "local":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

## Considerations
- HSTS should only be enabled when HTTPS is enforced.
- If a reverse proxy sets headers already, ensure no conflicts.

## Related Improvements
None.

---
*Identified: 2026-02-01*
