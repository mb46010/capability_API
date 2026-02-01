# BUG-002: Test Reload Fixtures Endpoint Missing Authentication

## Severity
🔴 CRITICAL

## Location
- **File(s)**: `src/api/routes/actions.py`
- **Line(s)**: 15-21

## Issue Description
The `/actions/test/reload-fixtures` endpoint allows any unauthenticated user to reload the Workday simulator's fixture data from disk. This endpoint is always available (not gated by environment variable).

```python
# ❌ VULNERABLE: No authentication, always exposed
@router.post("/test/reload-fixtures")
async def reload_fixtures(connector: ConnectorPort = Depends(get_connector)):
    """Reload fixture data without restarting server."""
    if isinstance(connector, WorkdaySimulator):
        connector.reload()
        return {"status": "reloaded", "type": "workday"}
    return {"status": "ignored", "reason": "not using workday simulator"}
```

## Impact
- **Data Manipulation**: If an attacker can modify fixture files on disk (e.g., via a separate vulnerability), they can force the application to load malicious data
- **Denial of Service**: Repeated reload calls can cause performance issues and interrupt ongoing operations
- **State Loss**: Reloading fixtures resets all in-memory state including pending requests, balances, and other mutable data
- **Production Exposure**: Unlike the demo reset endpoint, this is ALWAYS available, even in production

## Root Cause
The endpoint was intended for testing convenience but was placed in the main actions router without:
1. Environment gating (like `ENABLE_DEMO_RESET`)
2. Authentication requirements
3. Admin-only access control

## How to Fix

### Code Changes

```python
# ✅ FIXED: Add auth, admin check, and environment gate
from src.api.dependencies import get_current_principal
from src.adapters.auth import VerifiedPrincipal
from src.lib.config_validator import settings

@router.post("/test/reload-fixtures")
async def reload_fixtures(
    connector: ConnectorPort = Depends(get_connector),
    principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """Reload fixture data without restarting server. Admin + local/dev only."""
    # Environment check - only allow in local/dev
    if settings.ENVIRONMENT not in ["local", "dev"]:
        raise HTTPException(status_code=404, detail="Not found")

    # Admin check
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if isinstance(connector, WorkdaySimulator):
        connector.reload()
        return {"status": "reloaded", "type": "workday", "reloaded_by": principal.subject}
    return {"status": "ignored", "reason": "not using workday simulator"}
```

### Steps
1. Add authentication dependency to the endpoint
2. Add admin group check
3. Add environment restriction (local/dev only)
4. Return 404 in production to hide the endpoint's existence

## Verification

### Test Cases
1. Call endpoint without authentication - should return 401
2. Call endpoint as non-admin - should return 403
3. Call endpoint as admin in local environment - should succeed
4. In production environment, endpoint should return 404

### Verification Steps
```bash
# Without auth (should fail)
curl -X POST http://localhost:8000/actions/test/reload-fixtures

# With admin token (should succeed in local)
curl -X POST http://localhost:8000/actions/test/reload-fixtures \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Related Issues
- Related to BUG-001 (demo reset endpoint)

---
*Discovered: 2026-02-01*
