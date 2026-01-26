"""
Auth Adapter - OIDC Token Verification for HR AI Platform

This package provides:
- MockOktaProvider: A fully functional mock OIDC provider for local development
- TokenVerifier: Protocol and implementations for token validation
- VerifiedPrincipal: Domain object representing an authenticated identity

Usage (Local Development):
    from src.adapters.auth import MockOktaProvider, MockTokenVerifier

    provider = MockOktaProvider()
    verifier = MockTokenVerifier(provider)

    # Issue a token
    token = provider.issue_token(subject="admin@local.test")

    # Verify it
    principal = verifier.verify(token)
    print(f"Authenticated as: {principal.subject}")

Usage (Production):
    from src.adapters.auth import OktaTokenVerifier, AuthConfig, create_token_verifier

    config = AuthConfig.for_production(
        issuer="https://your-org.okta.com/oauth2/default",
        audience="api://hr-ai-platform",
    )
    verifier = create_token_verifier(config)

    # Verify incoming token
    principal = verifier.verify(token_from_request)
"""

from .mock_okta import (
    MockOktaProvider,
    MockUser,
    PrincipalType,
    TokenConfig,
    create_mock_okta_app,
)

from .verifier import (
    TokenVerifier,
    TokenVerificationError,
    VerifiedPrincipal,
    MockTokenVerifier,
    OktaTokenVerifier,
    AuthConfig,
    create_token_verifier,
    create_auth_dependency,
)

__all__ = [
    # Mock Okta
    "MockOktaProvider",
    "MockUser",
    "PrincipalType",
    "TokenConfig",
    "create_mock_okta_app",
    # Verifier
    "TokenVerifier",
    "TokenVerificationError",
    "VerifiedPrincipal",
    "MockTokenVerifier",
    "OktaTokenVerifier",
    "AuthConfig",
    "create_token_verifier",
    "create_auth_dependency",
]
