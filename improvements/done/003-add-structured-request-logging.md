# 003: Add Structured Request Logging Middleware

## Impact
**Effort**: Low (2 hours) | **Impact**: High | **Priority**: 1

## Location
- **File(s)**: `src/main.py`, `src/lib/logging.py` (new)
- **Component/Module**: FastAPI Middleware / Observability

## Current State

Request logging is minimal and unstructured. Only the audit logger captures events, and it's deep in the connector layer:

```python
# Only logging happens in connector/audit
self.audit_logger.log_event(event_type=action, payload=parameters, actor=...)
```

Missing from logs:
- HTTP request/response metadata (status, latency, path)
- Client information (IP, user agent)
- Request correlation across logs
- Error context at API boundary

## Proposed Improvement

Add structured JSON logging middleware that captures:
- Request: method, path, query params, client IP, user agent, request ID
- Response: status code, latency, content length
- Principal: subject, type, groups (from verified token)

## Benefits

- **Debugging**: Quickly trace issues with full request context
- **Monitoring**: Enable alerting on error rates, latency percentiles
- **Security**: Track access patterns, detect anomalies
- **Compliance**: Audit trail at API boundary

**Estimated value**: Reduces debugging time by 50%, enables proactive monitoring

## Implementation

### Approach
Add logging middleware that captures request/response metadata in structured JSON format.

### Estimated Effort
2 hours

### Steps
1. Create `src/lib/logging.py` with structured logger setup
2. Add request logging middleware to `main.py`
3. Include request_id correlation
4. Configure log level per environment

## Example

### Before
```python
# No request logging - only audit events deep in stack
```

### After
```python
# src/lib/logging.py
import logging
import json
from datetime import datetime, timezone

class StructuredFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "extra_data"):
            log_obj.update(record.extra_data)
        return json.dumps(log_obj)

def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logging.root.addHandler(handler)
    logging.root.setLevel(logging.INFO)
```

```python
# src/main.py
import time
import logging
from src.lib.context import get_request_id

request_logger = logging.getLogger("api.requests")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    latency_ms = (time.time() - start) * 1000

    request_logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "request_id": get_request_id(),
            }
        }
    )

    return response
```

**Sample log output:**
```json
{"timestamp": "2026-02-01T12:00:00Z", "level": "INFO", "logger": "api.requests", "message": "POST /actions/workday.hcm/get_employee 200", "method": "POST", "path": "/actions/workday.hcm/get_employee", "status_code": 200, "latency_ms": 45.2, "client_ip": "10.0.0.1", "request_id": "abc-123"}
```

## Considerations

- Don't log request/response bodies (PII concerns, size)
- Consider separate log files for requests vs application logs
- Add log rotation configuration
- Integrate with centralized logging (ELK, Datadog, etc.)

## Related Improvements
- 001-add-request-timeout-middleware.md (log timeout events)

---
*Identified: 2026-02-01*
