# BUG-002: Reload fixtures endpoint is unauthenticated

## Severity
🟠 HIGH

## Location
- **File(s)**: src/api/routes/actions.py
- **Line(s)**: 15-21

## Issue Description
`POST /actions/test/reload-fixtures` is exposed without authentication or environment gating. Anyone with network access can reset Workday simulator state, which can erase evidence, change test outcomes, or disrupt running demos/integrations.

## Impact
- Unauthorized users can mutate system state and invalidate audit/verification flows.
- Potential denial-of-service or data inconsistency during demos or tests.

## Root Cause
The endpoint is not protected by `get_current_principal`, group checks, or an environment guard.

## How to Fix

### Code Changes
- Require authentication and restrict to admins.
- Gate endpoint behind `ENVIRONMENT=local` or a feature flag like `ENABLE_DEMO_RESET`.

Example direction:
```python
@router.post("/test/reload-fixtures")
async def reload_fixtures(
    connector: ConnectorPort = Depends(get_connector),
    principal: VerifiedPrincipal = Depends(get_current_principal),
):
    if settings.ENVIRONMENT != "local":
        raise HTTPException(status_code=403, detail="Not available")
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")
    ...
```

### Steps
1. Add auth dependency and group check.
2. Add environment/feature-flag guard.
3. Add tests for unauthorized access.

## Verification

### Test Cases
- Unauthenticated request returns 401.
- Authenticated non-admin request returns 403.
- Admin request in local environment succeeds.
- Admin request in non-local returns 403.

### Verification Steps
1. Call endpoint without a token → expect 401.
2. Call with a non-admin token → expect 403.
3. Call with admin token in local → expect 200.

## Related Issues
None.

---
*Discovered: 2026-02-01*
