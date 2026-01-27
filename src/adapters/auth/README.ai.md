# Module Context: Auth Adapter

**AI Facts for Coding Agents**

## Purpose
Identity verification and token management. Provides a mock OIDC provider for local development.

## Key Exports
- `MockOktaProvider`: Issues cryptographically valid RSA-signed JWTs.
- `MockTokenVerifier`: Validates tokens against the mock provider.
- `VerifiedPrincipal`: Domain object representing an authenticated identity.

## Dependency Graph (Functional)
- **Imports**: `src.adapters.auth.mock_okta`, `src.adapters.auth.verifier`.
- **External**: `PyJWT`, `cryptography`.

## Architectural Constraints
- MUST NOT store real credentials.
- Issued tokens SHOULD match the structure of real Okta OIDC tokens.
- Verifier MUST extract `principal_type` and `groups` for policy evaluation.
