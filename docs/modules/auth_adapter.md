# Auth Adapter

Identity verification and token management for the Capability API. This module provides a mock OIDC provider for local development and a verifier for JWT tokens.

## Key Components

- **MockOktaProvider**: Issues cryptographically valid RSA-signed JWTs.
- **MockTokenVerifier**: Validates tokens against the mock provider.
- **VerifiedPrincipal**: Domain object representing an authenticated identity.

## Dependencies

- **Internal**: `src.adapters.auth.mock_okta`, `src.adapters.auth.verifier`.
- **External**: `PyJWT`, `cryptography`.

## Architectural Constraints

- MUST NOT store real credentials.
- Issued tokens SHOULD match the structure of real Okta OIDC tokens.
- Verifier MUST extract `principal_type` and `groups` for policy evaluation.
- Test endpoints (`/test/tokens`, `/test/users`) MUST require the `X-Test-Secret` header, configured via `MOCK_OKTA_TEST_SECRET`.

## Policy Schema

For detailed information on how policies are structured and validated, see [Policy Schema](../policy_schema.md).
