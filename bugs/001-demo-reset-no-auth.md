# BUG-001: Demo Reset Endpoint Missing Authentication

## Severity
🔴 CRITICAL

## Location
- **File(s)**: `src/api/routes/demo.py`
- **Line(s)**: 6-19

## Issue Description
The `/demo/reset` endpoint is exposed without any authentication. When `ENABLE_DEMO_RESET=true`, any unauthenticated client can call this endpoint to clear all service caches (`lru_cache`) including the policy engine, connector, and flow runner.

```python
# ❌ VULNERABLE: No authentication required
@router.post("/reset")
async def reset_services():
    """Clear lru_caches for core services..."""
    get_policy_engine.cache_clear()
    get_connector.cache_clear()
    get_flow_runner_adapter.cache_clear()
    return {...}
```

## Impact
- **Denial of Service**: An attacker can repeatedly call this endpoint to force constant re-initialization of services, causing performance degradation
- **State Manipulation**: Clearing caches forces reload of policies and fixtures, potentially causing race conditions
- **Data Loss**: In-memory state in the WorkdaySimulator (idempotency cache, requests, etc.) could be lost
- **Security Bypass**: If policy files are modified on disk, forcing a reload could load malicious policies

## Root Cause
The endpoint was designed for demo/development convenience but lacks the authentication dependency (`get_current_principal`) that protects other endpoints. While it's gated by an environment variable, this doesn't prevent access once enabled.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Add authentication and admin check
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_current_principal, get_policy_engine, get_connector, get_flow_runner_adapter
from src.adapters.auth import VerifiedPrincipal

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/reset")
async def reset_services(
    principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """
    Clear lru_caches for core services to force re-initialization.
    Admin access required.
    """
    # Require admin group membership
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")

    get_policy_engine.cache_clear()
    get_connector.cache_clear()
    get_flow_runner_adapter.cache_clear()

    return {
        "status": "reset",
        "reset_by": principal.subject,
        "message": "Service caches cleared. Next request will re-initialize dependencies."
    }
```

### Steps
1. Add `get_current_principal` import from dependencies
2. Add `principal: VerifiedPrincipal = Depends(get_current_principal)` parameter to the endpoint
3. Add admin group check before clearing caches
4. Include audit information (who performed the reset) in the response

## Verification

### Test Cases
1. Call `/demo/reset` without authentication - should return 401
2. Call `/demo/reset` with a non-admin token - should return 403
3. Call `/demo/reset` with an admin token - should succeed with 200

### Verification Steps
1. Run `curl -X POST http://localhost:8000/demo/reset` - verify 401 response
2. Get a user token and call the endpoint - verify 403 response
3. Get an admin token and call the endpoint - verify success

## Related Issues
- Related to BUG-002 (test reload endpoint also lacks auth)

---
*Discovered: 2026-02-01*
