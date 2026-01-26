"""
Token Verifier - Hexagonal Port for OIDC Token Validation

This module defines the port (interface) for token verification and provides
adapters for both mock (local development) and real Okta (production).

The Capability API depends only on the TokenVerifier protocol, allowing us to
swap implementations without changing business logic.

Architecture:
    TokenVerifier (Protocol)
        ├── MockTokenVerifier (uses MockOktaProvider directly)
        └── OktaTokenVerifier (validates against real Okta JWKS)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol, Optional

import httpx
import jwt
from jwt import PyJWKClient

from .mock_okta import MockOktaProvider, PrincipalType


class TokenVerificationError(Exception):
    """Raised when token verification fails."""

    def __init__(self, message: str, error_code: str = "invalid_token"):
        super().__init__(message)
        self.error_code = error_code


@dataclass
class VerifiedPrincipal:
    """
    Represents a verified identity extracted from a valid token.

    This is the "domain object" that the Capability API works with,
    decoupled from the raw JWT claims.
    """

    subject: str
    principal_type: PrincipalType
    groups: list[str]
    issuer: str
    audience: str
    expires_at: int
    issued_at: int
    token_id: str | None = None
    email: str | None = None
    name: str | None = None
    mfa_verified: bool = False
    raw_claims: dict[str, Any] | None = None

    @property
    def is_human(self) -> bool:
        return self.principal_type == PrincipalType.HUMAN

    @property
    def is_machine(self) -> bool:
        return self.principal_type == PrincipalType.MACHINE

    @property
    def is_ai_agent(self) -> bool:
        return self.principal_type == PrincipalType.AI_AGENT

    def has_group(self, group: str) -> bool:
        """Check if principal belongs to a specific group."""
        return group in self.groups

    def time_until_expiry(self) -> int:
        """Seconds until token expires (negative if already expired)."""
        return self.expires_at - int(time.time())


class TokenVerifier(Protocol):
    """
    Protocol (interface) for token verification.

    Implementations must verify the token signature, validate standard claims
    (iss, aud, exp, iat), and extract principal information.
    """

    def verify(self, token: str) -> VerifiedPrincipal:
        """
        Verify a token and extract the principal.

        Args:
            token: The raw JWT string (without "Bearer " prefix)

        Returns:
            VerifiedPrincipal with extracted identity information

        Raises:
            TokenVerificationError: If token is invalid, expired, or revoked
        """
        ...

    def get_issuer(self) -> str:
        """Get the expected token issuer."""
        ...


class MockTokenVerifier:
    """
    Token verifier for local development using MockOktaProvider.

    This verifier uses the same RSA key pair as the mock provider,
    so tokens issued by MockOktaProvider will validate correctly.
    """

    def __init__(self, provider: MockOktaProvider):
        self._provider = provider

    def verify(self, token: str) -> VerifiedPrincipal:
        """Verify token using the mock provider."""
        try:
            claims = self._provider.verify_token(token)
            return self._claims_to_principal(claims)
        except jwt.ExpiredSignatureError:
            raise TokenVerificationError("Token has expired", "token_expired")
        except jwt.InvalidAudienceError:
            raise TokenVerificationError("Invalid audience", "invalid_audience")
        except jwt.InvalidIssuerError:
            raise TokenVerificationError("Invalid issuer", "invalid_issuer")
        except jwt.InvalidTokenError as e:
            # Check the error message to provide more specific error codes
            error_msg = str(e).lower()
            if "issuer" in error_msg:
                raise TokenVerificationError(str(e), "invalid_issuer")
            elif "audience" in error_msg:
                raise TokenVerificationError(str(e), "invalid_audience")
            raise TokenVerificationError(str(e), "invalid_token")

    def get_issuer(self) -> str:
        return self._provider.issuer

    def _claims_to_principal(self, claims: dict[str, Any]) -> VerifiedPrincipal:
        """Convert raw JWT claims to VerifiedPrincipal."""
        # Parse principal type
        principal_type_str = claims.get("principal_type", "HUMAN")
        try:
            principal_type = PrincipalType(principal_type_str)
        except ValueError:
            principal_type = PrincipalType.HUMAN

        # Check for MFA
        amr = claims.get("amr", [])
        mfa_verified = "mfa" in amr

        return VerifiedPrincipal(
            subject=claims["sub"],
            principal_type=principal_type,
            groups=claims.get("groups", []),
            issuer=claims["iss"],
            audience=claims["aud"],
            expires_at=claims["exp"],
            issued_at=claims["iat"],
            token_id=claims.get("jti"),
            email=claims.get("email"),
            name=claims.get("name"),
            mfa_verified=mfa_verified,
            raw_claims=claims,
        )


class OktaTokenVerifier:
    """
    Token verifier for production using real Okta.

    This verifier fetches JWKS from Okta's well-known endpoint and caches
    the public keys for efficient verification.
    """

    def __init__(
        self,
        issuer: str,
        audience: str,
        client_id: str | None = None,
        jwks_cache_ttl: int = 300,  # 5 minutes
    ):
        self._issuer = issuer
        self._audience = audience
        self._client_id = client_id

        # Construct JWKS URI from issuer
        jwks_uri = f"{issuer.rstrip('/')}/v1/keys"
        self._jwk_client = PyJWKClient(jwks_uri, cache_jwk_set=True, lifespan=jwks_cache_ttl)

    def verify(self, token: str) -> VerifiedPrincipal:
        """Verify token against real Okta JWKS."""
        try:
            # Get the signing key from JWKS
            signing_key = self._jwk_client.get_signing_key_from_jwt(token)

            # Decode and verify
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=self._audience,
                issuer=self._issuer,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_aud": True,
                    "require": ["exp", "iat", "iss", "sub", "aud"],
                },
            )

            return self._claims_to_principal(claims)

        except jwt.ExpiredSignatureError:
            raise TokenVerificationError("Token has expired", "token_expired")
        except jwt.InvalidAudienceError:
            raise TokenVerificationError("Invalid audience", "invalid_audience")
        except jwt.InvalidIssuerError:
            raise TokenVerificationError("Invalid issuer", "invalid_issuer")
        except jwt.PyJWKClientError as e:
            raise TokenVerificationError(f"Failed to fetch JWKS: {e}", "jwks_error")
        except jwt.InvalidTokenError as e:
            raise TokenVerificationError(str(e), "invalid_token")

    def get_issuer(self) -> str:
        return self._issuer

    def _claims_to_principal(self, claims: dict[str, Any]) -> VerifiedPrincipal:
        """Convert raw JWT claims to VerifiedPrincipal."""
        # Parse principal type (custom claim)
        principal_type_str = claims.get("principal_type", "HUMAN")
        try:
            principal_type = PrincipalType(principal_type_str)
        except ValueError:
            principal_type = PrincipalType.HUMAN

        # Check for MFA in AMR claim
        amr = claims.get("amr", [])
        mfa_verified = "mfa" in amr

        return VerifiedPrincipal(
            subject=claims["sub"],
            principal_type=principal_type,
            groups=claims.get("groups", []),
            issuer=claims["iss"],
            audience=claims["aud"],
            expires_at=claims["exp"],
            issued_at=claims["iat"],
            token_id=claims.get("jti"),
            email=claims.get("email"),
            name=claims.get("name"),
            mfa_verified=mfa_verified,
            raw_claims=claims,
        )


# ---------------------------------------------------------------------------
# Factory for creating the appropriate verifier
# ---------------------------------------------------------------------------


@dataclass
class AuthConfig:
    """Configuration for authentication."""

    mode: str = "mock"  # "mock" or "okta"
    issuer: str = "http://localhost:9000/oauth2/default"
    audience: str = "api://hr-ai-platform"
    client_id: str | None = None

    @classmethod
    def for_local_development(cls) -> "AuthConfig":
        """Create config for local development with mock Okta."""
        return cls(
            mode="mock",
            issuer="http://localhost:9000/oauth2/default",
            audience="api://hr-ai-platform",
        )

    @classmethod
    def for_production(
        cls, issuer: str, audience: str, client_id: str | None = None
    ) -> "AuthConfig":
        """Create config for production with real Okta."""
        return cls(
            mode="okta",
            issuer=issuer,
            audience=audience,
            client_id=client_id,
        )


def create_token_verifier(
    config: AuthConfig, mock_provider: MockOktaProvider | None = None
) -> TokenVerifier:
    """
    Factory function to create the appropriate token verifier.

    Args:
        config: Authentication configuration
        mock_provider: Optional MockOktaProvider instance (required if mode="mock")

    Returns:
        TokenVerifier instance
    """
    if config.mode == "mock":
        if mock_provider is None:
            mock_provider = MockOktaProvider(
                issuer=config.issuer,
                audience=config.audience,
            )
        return MockTokenVerifier(mock_provider)
    elif config.mode == "okta":
        return OktaTokenVerifier(
            issuer=config.issuer,
            audience=config.audience,
            client_id=config.client_id,
        )
    else:
        raise ValueError(f"Unknown auth mode: {config.mode}")


# ---------------------------------------------------------------------------
# FastAPI Dependency for token verification
# ---------------------------------------------------------------------------


def create_auth_dependency(verifier: TokenVerifier):
    """
    Create a FastAPI dependency for token verification.

    Usage:
        verifier = create_token_verifier(config)
        get_principal = create_auth_dependency(verifier)

        @app.get("/protected")
        async def protected_endpoint(principal: VerifiedPrincipal = Depends(get_principal)):
            return {"user": principal.subject}
    """
    from fastapi import Depends, HTTPException, Header

    async def get_verified_principal(
        authorization: Optional[str] = Header(None, description="Bearer token")
    ) -> VerifiedPrincipal:
        if not authorization:
            raise HTTPException(
                status_code=401,
                detail="Missing authorization header",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="Invalid authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:]  # Strip "Bearer "

        try:
            return verifier.verify(token)
        except TokenVerificationError as e:
            raise HTTPException(
                status_code=401,
                detail=e.error_code,
                headers={"WWW-Authenticate": f'Bearer error="{e.error_code}"'},
            )

    return get_verified_principal
