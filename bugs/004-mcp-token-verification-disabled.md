# BUG-004: MCP Server Token Verification Disabled

## Severity
🟠 HIGH

## Location
- **File(s)**: `src/mcp/adapters/auth.py`
- **Line(s)**: 21-39

## Issue Description
The MCP server's `extract_principal` function decodes JWT tokens with signature verification disabled. While the comment states "backend will verify", this creates a security gap where the MCP server makes authorization decisions based on unverified claims.

```python
# ❌ VULNERABLE: No signature verification
def extract_principal(token: str) -> Optional[PrincipalContext]:
    try:
        # Decode without verification - backend will verify.
        payload = jwt.decode(token, options={"verify_signature": False})

        return PrincipalContext(
            subject=payload.get("sub", "unknown"),
            principal_type=payload.get("principal_type", "HUMAN"),
            groups=payload.get("groups", []),
            mfa_verified=mfa_verified,
            raw_token=token
        )
```

The extracted principal is then used in `is_tool_allowed()` to make RBAC decisions:

```python
# Authorization decisions based on unverified claims
def is_tool_allowed(principal: PrincipalContext, tool_name: str) -> bool:
    role = principal.principal_type  # Unverified claim!
    if role == "HUMAN":
        if "hr-platform-admins" in principal.groups:  # Unverified claim!
            role = "ADMIN"
```

## Impact
- **Privilege Escalation**: An attacker can craft a fake JWT with admin groups or any principal type, and the MCP server will grant elevated tool access
- **RBAC Bypass**: The `is_tool_allowed` check uses unverified claims to determine access to sensitive tools like `get_compensation`, `approve_time_off`
- **Defense in Depth Failure**: Even though the backend verifies the token, the MCP layer's authorization has already been bypassed

## Root Cause
The design assumed that because the Capability API backend verifies tokens, the MCP layer doesn't need to. However:
1. The MCP layer makes its own authorization decisions via `is_tool_allowed()`
2. An attacker can see tool responses, error messages, and behavior based on unverified roles
3. Information leakage occurs even if the backend blocks the final request

## How to Fix

### Code Changes

**Option A: Verify token signature in MCP layer**
```python
# ✅ FIXED: Verify token signature
from src.mcp.lib.config import settings
from jwt import PyJWKClient

_jwk_client = None

def get_jwk_client():
    global _jwk_client
    if _jwk_client is None:
        jwks_uri = f"{settings.OKTA_ISSUER}/v1/keys"
        _jwk_client = PyJWKClient(jwks_uri, cache_jwk_set=True, lifespan=300)
    return _jwk_client

def extract_principal(token: str) -> Optional[PrincipalContext]:
    try:
        # Verify signature using JWKS
        jwk_client = get_jwk_client()
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.CAPABILITY_API_AUDIENCE,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": True,
            }
        )
        # ... rest of function
```

**Option B: Remove RBAC checks from MCP layer (rely fully on backend)**
```python
# ✅ FIXED: Remove RBAC checks, let backend handle all authorization
def is_tool_allowed(principal: PrincipalContext, tool_name: str) -> bool:
    """
    Removed local RBAC. Backend policy engine handles all authorization.
    This function now only validates token structure, not permissions.
    """
    return True  # Backend will enforce

# Then ensure ALL tools pass through backend API with proper auth
```

### Steps
1. Choose between Option A (verify at MCP layer) or Option B (remove RBAC from MCP)
2. If Option A:
   - Add JWKS client initialization
   - Update `extract_principal` to verify signature
   - Handle verification failures appropriately
3. If Option B:
   - Remove or simplify `is_tool_allowed`
   - Ensure all tools call backend with proper auth headers
   - Update error handling to surface backend authorization errors

## Verification

### Test Cases
1. Send a forged JWT with admin groups to MCP server
   - Before fix: MCP grants admin-level tool access
   - After fix: MCP rejects invalid token (Option A) or backend rejects (Option B)
2. Send an expired token
   - Should be rejected at MCP layer (Option A) or backend (Option B)
3. Valid token should continue to work normally

### Verification Steps
```bash
# Create a forged token (no valid signature)
FORGED_TOKEN=$(python3 -c "import jwt; print(jwt.encode({'sub': 'attacker', 'groups': ['hr-platform-admins'], 'principal_type': 'HUMAN', 'exp': 9999999999}, 'fake-secret', algorithm='HS256'))")

# Try to call a protected MCP tool
# Before fix: May succeed at MCP layer or reveal admin-only behavior
# After fix: Should fail with authentication error
```

## Related Issues
- Related to BUG-005 (sensitive data in logs)

---
*Discovered: 2026-02-01*
