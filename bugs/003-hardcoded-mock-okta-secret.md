# BUG-003: Hardcoded Default Secret for Mock Okta Test Endpoints

## Severity
🟠 HIGH

## Location
- **File(s)**: `src/lib/config_validator.py`
- **Line(s)**: 20

## Issue Description
The Mock Okta test secret has a hardcoded default value that is used if the environment variable is not set. This secret protects administrative endpoints in the mock Okta provider (`/test/users`, `/test/tokens`).

```python
# ❌ VULNERABLE - Hardcoded default secret
MOCK_OKTA_TEST_SECRET: str = Field(default="mock-okta-secret", description="Secret key for Mock Okta test endpoints")
```

While the mock Okta provider is intended for local development, if inadvertently enabled in a non-local environment (or if someone exposes their local instance), an attacker knowing this default can:
- Create arbitrary test users
- Issue tokens with any claims (groups, principal_type, etc.)
- Bypass authentication entirely

## Impact
- **Authentication bypass**: Attacker can create admin tokens
- **Privilege escalation**: Can create tokens with `hr-platform-admins` group
- **System compromise**: Full access to all Capability API endpoints

## Root Cause
The default value allows the system to function out-of-the-box for local development without configuration. However, this creates a risk if the development configuration is accidentally deployed or exposed.

## How to Fix

### Code Changes
Either require the secret explicitly or generate a random one:

```python
# ✅ FIXED - Option 1: Require explicit configuration (errors if not set)
MOCK_OKTA_TEST_SECRET: str = Field(description="Secret key for Mock Okta test endpoints")

# ✅ FIXED - Option 2: Generate random secret per-run
import secrets
MOCK_OKTA_TEST_SECRET: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
```

### Steps
1. Update `src/lib/config_validator.py` to remove the hardcoded default
2. Update documentation to require setting `MOCK_OKTA_TEST_SECRET` in `.env`
3. Add validation that errors out if mock Okta is enabled without a proper secret
4. Update CI/CD to ensure secrets are provided in test environments

## Verification

### Test Cases
1. Start the application without `MOCK_OKTA_TEST_SECRET` set - should error or use random
2. Verify test endpoints reject the old default value "mock-okta-secret"
3. Verify endpoints work with properly configured secret

### Verification Steps
1. Remove `MOCK_OKTA_TEST_SECRET` from environment
2. Attempt to start application (should fail or use random)
3. Set a strong secret and verify test endpoints work

## Related Issues
- None

---
*Discovered: 2026-02-03*
