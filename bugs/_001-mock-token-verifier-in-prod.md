# BUG-001: Mock token verifier used for all environments

## Severity
🔴 CRITICAL

## Location
- **File(s)**: src/api/dependencies.py
- **Line(s)**: 15-18

## Issue Description
The API dependency wiring always constructs a `MockOktaProvider` and `MockTokenVerifier` regardless of environment. This means production and dev deployments accept tokens signed by the mock provider rather than a real Okta JWKS. Any attacker who can mint a mock token (or reuses the repo’s mock issuer defaults) can authenticate as arbitrary principals.

## Impact
- Complete authentication bypass in non-local environments.
- Unauthorized access to all protected endpoints, potentially including HR actions and flows.
- Compliance and audit violations due to unauthenticated access.

## Root Cause
Auth dependencies are hardcoded to the mock implementation instead of selecting a verifier based on environment/config.

## How to Fix

### Code Changes
- Replace the hardcoded mock verifier with a configuration-driven verifier using `AuthConfig` and `create_token_verifier`.
- Use the mock verifier only for `ENVIRONMENT=local` (or explicit `AUTH_MODE=mock`).

Example direction:
```python
# ❌ current
provider = MockOktaProvider()
verifier = MockTokenVerifier(provider)
get_current_principal = create_auth_dependency(verifier)

# ✅ suggested
from src.adapters.auth import AuthConfig, create_token_verifier

auth_config = AuthConfig.from_env()
verifier = create_token_verifier(auth_config, mock_provider=provider_if_needed)
get_current_principal = create_auth_dependency(verifier)
```

### Steps
1. Add auth configuration (issuer, audience, mode) to settings or environment variables.
2. Create the verifier via `create_token_verifier` in `src/api/dependencies.py`.
3. Ensure mock provider is only constructed in local/test modes.
4. Update deployment docs to require issuer/audience env vars in non-local environments.

## Verification

### Test Cases
- With `ENVIRONMENT=prod` and real Okta issuer/audience, a mock token should be rejected (401).
- With `ENVIRONMENT=local`, mock tokens should still be accepted.

### Verification Steps
1. Set prod-like env vars and run the API.
2. Call a protected endpoint with a mock token → expect 401.
3. Call with a real Okta token (or test JWKS) → expect 200.

## Related Issues
None.

---
*Discovered: 2026-02-01*
