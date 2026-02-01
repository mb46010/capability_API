# BUG-003: Mock Okta Test Endpoints Exposed Without Authentication

## Severity
🟠 HIGH

## Location
- **File(s)**: `src/adapters/auth/mock_okta.py`
- **Line(s)**: 771-815

## Issue Description
The Mock Okta provider exposes test/admin endpoints (`/test/users`, `/test/tokens`) that allow anyone to:
1. Create arbitrary test users with any principal type and group memberships
2. Generate tokens directly without OAuth flows
3. Query user information

These endpoints are mounted at `/auth/test/*` when running in local environment.

```python
# ❌ VULNERABLE: No authentication on admin endpoints
@app.post("/test/users")
async def create_test_user(request_data: CreateUserRequest):
    """Create a test user (admin endpoint for testing)."""
    user = MockUser(...)
    provider.register_user(user)
    return {"status": "created", "subject": user.subject}

@app.post("/test/tokens")
async def create_test_token(request_data: CreateTokenRequest):
    """Create a token directly (bypassing OAuth flows)."""
    token = provider.issue_token(...)
    return {"access_token": token, "token_type": "Bearer"}
```

## Impact
- **Privilege Escalation**: Anyone can create tokens with admin groups or any principal type
- **Authentication Bypass**: Tokens can be created without going through proper OAuth flows
- **Policy Bypass**: Attacker can create tokens with custom claims to bypass policy conditions
- **Local Development Risk**: While this is "local only", developers often run local against real data or test systems

## Root Cause
These endpoints were designed for test automation but lack:
1. Any form of authentication
2. Environment-specific safeguards beyond the mount condition
3. Rate limiting or logging

## How to Fix

### Code Changes

**Option A: Add a secret key requirement**
```python
# ✅ FIXED: Require test secret key
import os

TEST_SECRET = os.getenv("MOCK_OKTA_TEST_SECRET")

@app.post("/test/users")
async def create_test_user(
    request_data: CreateUserRequest,
    x_test_secret: str = Header(None, alias="X-Test-Secret")
):
    """Create a test user (requires test secret)."""
    if not TEST_SECRET or x_test_secret != TEST_SECRET:
        raise HTTPException(status_code=403, detail="Invalid test secret")

    user = MockUser(...)
    provider.register_user(user)
    return {"status": "created", "subject": user.subject}
```

**Option B: Remove from mounted app, provide only via direct provider access**
```python
# ✅ FIXED: Only expose via programmatic API, not HTTP
def create_mock_okta_app(provider: MockOktaProvider | None = None):
    # ... OIDC endpoints only ...

    # Test endpoints removed from HTTP surface
    # Tests use provider.register_user() and provider.issue_token() directly
```

### Steps
1. Decide on protection strategy (secret key or remove HTTP endpoints)
2. For secret key approach:
   - Add `MOCK_OKTA_TEST_SECRET` environment variable
   - Require the header on test endpoints
   - Document in `.env.example`
3. For removal approach:
   - Remove `/test/*` routes from FastAPI app
   - Update test code to use provider directly

## Verification

### Test Cases
1. If using secret key: call `/auth/test/users` without secret - should return 403
2. If using secret key: call with valid secret - should succeed
3. If removed: call `/auth/test/users` - should return 404
4. Verify existing tests still work after changes

### Verification Steps
```bash
# Verify endpoint is protected (secret key approach)
curl -X POST http://localhost:8000/auth/test/users \
  -H "Content-Type: application/json" \
  -d '{"subject": "attacker@evil.com", "groups": ["hr-platform-admins"]}'
# Should return 403

# With secret (should succeed)
curl -X POST http://localhost:8000/auth/test/users \
  -H "Content-Type: application/json" \
  -H "X-Test-Secret: $MOCK_OKTA_TEST_SECRET" \
  -d '{"subject": "test@local.test"}'
```

## Related Issues
- None

---
*Discovered: 2026-02-01*
