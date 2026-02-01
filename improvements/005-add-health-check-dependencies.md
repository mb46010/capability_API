# 005: Enhance Health Check with Dependency Details

## Impact
**Effort**: Low (1-2 hours) | **Impact**: Medium | **Priority**: 2

## Location
- **File(s)**: `src/main.py`
- **Component/Module**: Health Check Endpoint

## Current State

The health check endpoint exists but only verifies that dependencies are "not None":

```python
@app.get("/health")
async def health_check(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    connector: ConnectorPort = Depends(get_connector)
):
    # Simple existence check
    if policy_engine.policy:
        health_status["dependencies"]["policy_engine"] = "ok"

    if connector:
        health_status["dependencies"]["connector"] = "ok"
```

Missing:
- Actual connectivity tests (can connector reach fixtures?)
- Response time measurements
- Version/config information
- Detailed error messages

## Proposed Improvement

Enhance health check to:
1. Actually exercise dependencies (lightweight probe)
2. Report response times
3. Include version and configuration info
4. Provide structured status for monitoring

## Benefits

- **Reliability**: Catch problems before users do
- **Debugging**: Quick status overview for operators
- **Monitoring**: Structured data for alerting systems
- **Deployment**: Better readiness probes for k8s

**Estimated value**: Faster incident detection, reduced MTTR

## Implementation

### Approach
Add lightweight probe calls to each dependency and time them. Include version info.

### Estimated Effort
1-2 hours

### Steps
1. Add version constant or read from package
2. Add probe methods to dependencies
3. Time each probe in health check
4. Return detailed structured response

## Example

### Before
```python
@app.get("/health")
async def health_check(...):
    health_status = {
        "status": "ok",
        "dependencies": {
            "policy_engine": "unknown",
            "connector": "unknown"
        }
    }
    if policy_engine.policy:
        health_status["dependencies"]["policy_engine"] = "ok"
    if connector:
        health_status["dependencies"]["connector"] = "ok"
    return health_status
```

### After
```python
import time
from src import __version__

@app.get("/health")
async def health_check(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    connector: ConnectorPort = Depends(get_connector)
):
    start = time.time()
    health_status = {
        "status": "ok",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "checks": {},
        "response_time_ms": 0
    }

    # Policy Engine Check
    pe_start = time.time()
    try:
        policy_count = len(policy_engine.policy.policies)
        health_status["checks"]["policy_engine"] = {
            "status": "ok",
            "policy_count": policy_count,
            "response_time_ms": round((time.time() - pe_start) * 1000, 2)
        }
    except Exception as e:
        health_status["checks"]["policy_engine"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    # Connector Check (lightweight probe)
    conn_start = time.time()
    try:
        # Check employee count as lightweight probe
        employee_count = len(connector.employees) if hasattr(connector, 'employees') else 0
        health_status["checks"]["connector"] = {
            "status": "ok",
            "type": type(connector).__name__,
            "employee_count": employee_count,
            "response_time_ms": round((time.time() - conn_start) * 1000, 2)
        }
    except Exception as e:
        health_status["checks"]["connector"] = {
            "status": "error",
            "error": str(e)
        }
        health_status["status"] = "degraded"

    health_status["response_time_ms"] = round((time.time() - start) * 1000, 2)

    if health_status["status"] != "ok":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status
```

**Sample response:**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "local",
  "checks": {
    "policy_engine": {
      "status": "ok",
      "policy_count": 25,
      "response_time_ms": 0.5
    },
    "connector": {
      "status": "ok",
      "type": "WorkdaySimulator",
      "employee_count": 5,
      "response_time_ms": 1.2
    }
  },
  "response_time_ms": 2.1
}
```

## Considerations

- Keep probes lightweight (<100ms total)
- Don't expose sensitive config in response
- Consider separate liveness vs readiness probes
- Add caching to prevent probe from overloading dependencies

## Related Improvements
- 003-add-structured-request-logging.md

---
*Identified: 2026-02-01*
