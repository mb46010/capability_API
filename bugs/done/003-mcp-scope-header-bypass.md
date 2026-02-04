# BUG-003: MCP-Scoped Tokens Can Bypass Direct API Restriction via Spoofed Header

## Severity
🟠 HIGH

## Location
- **File(s)**: src/domain/services/action_service.py, src/api/routes/actions.py
- **Line(s)**: src/domain/services/action_service.py:94-105, src/api/routes/actions.py:51-76

## Issue Description
The direct-API restriction for MCP-scoped tokens relies solely on the presence of the `X-Acting-Through` header. Because headers are client-controlled, any caller holding an MCP-scoped token can spoof this header and call the Capability API directly, bypassing the intended restriction that MCP tokens should only be used via the MCP server.

**Current behavior:**
```python
# ❌ VULNERABLE
if "mcp:use" in scopes and not acting_through:
    raise HTTPException(
        status_code=403,
        detail="MCP-scoped tokens cannot be used for direct API access"
    )
```

This treats any request with `X-Acting-Through` as trustworthy without cryptographic verification.

## Impact
- MCP-scoped tokens can be used directly against the API if the caller adds a header.
- Undermines separation between MCP access and direct API access.
- Potentially broadens the attack surface if MCP tokens have different scopes or lifetimes.

## Root Cause
Authorization relies on an untrusted, client-supplied header rather than a verifiable token claim or trusted network boundary.

## How to Fix

### Code Changes
Use token claims to validate MCP origin (e.g., `cid`/`azp`/`client_id` or a dedicated `acting_through` claim), and optionally also validate `X-Acting-Through` against that claim. Do not treat the header alone as proof.

```python
# ✅ FIXED (example)
if "mcp:use" in scopes:
    mcp_client_id = settings.MCP_CLIENT_ID
    token_client_id = token_claims.get("cid") or token_claims.get("azp") or token_claims.get("client_id")
    if token_client_id != mcp_client_id:
        raise HTTPException(
            status_code=403,
            detail="MCP-scoped tokens must originate from MCP client"
        )
```

### Steps
1. Add a configured MCP client identifier (e.g., `MCP_CLIENT_ID`) in settings.
2. Validate MCP tokens using a trusted claim (`cid`/`azp`/`client_id` or a custom claim) instead of a header.
3. Optionally require `X-Acting-Through` to match the claim for audit visibility, but do not rely on it for auth.

## Verification

### Test Cases
- MCP token without header should be rejected.
- MCP token with spoofed header but wrong client claim should be rejected.
- MCP token with correct client claim should be accepted.

### Verification Steps
1. Issue an MCP token for a non-MCP client and call `/actions/...` with `X-Acting-Through: mcp-server`.
2. Confirm the request is rejected with 403.
3. Issue a valid MCP token for the MCP client and confirm the request succeeds.

## Related Issues
- None.

---
*Discovered: 2026-02-02T22:06:45Z*
