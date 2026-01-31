"""
Mock Okta OIDC Provider for Local Development

This module provides a realistic mock of Okta's OIDC functionality for local
development and testing. It implements:

1. OIDC Discovery (/.well-known/openid-configuration)
2. JWKS endpoint (/oauth2/v1/keys)
3. Token endpoint (/oauth2/v1/token)
4. Token introspection (/oauth2/v1/introspect)
5. Userinfo endpoint (/oauth2/v1/userinfo)

The mock issues cryptographically valid JWTs signed with RSA keys, so the
Capability API can validate tokens using the same code path as production.

Usage:
    # Standalone server
    python -m src.adapters.auth.mock_okta --port 9000

    # Programmatic (for tests)
    from src.adapters.auth.mock_okta import MockOktaProvider
    provider = MockOktaProvider()
    token = provider.issue_token(subject="user@example.com", principal_type="HUMAN")
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, List, Dict

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import jwt
from pydantic import BaseModel


class PrincipalType(str, Enum):
    """Principal types as defined in the policy schema."""

    HUMAN = "HUMAN"
    MACHINE = "MACHINE"
    AI_AGENT = "AI_AGENT"


# ---------------------------------------------------------------------------
# Pydantic Models for API Requests
# ---------------------------------------------------------------------------


class CreateUserRequest(BaseModel):
    """Request model for creating a test user."""
    subject: str
    principal_type: str = "HUMAN"
    groups: List[str] = []
    name: Optional[str] = None
    email: Optional[str] = None
    mfa_verified: bool = False
    custom_claims: Dict[str, Any] = {}


class CreateTokenRequest(BaseModel):
    """Request model for creating a test token."""
    subject: str
    principal_type: Optional[str] = None
    groups: Optional[List[str]] = None
    ttl_seconds: Optional[int] = None
    additional_claims: Optional[Dict[str, Any]] = None


@dataclass
class MockUser:
    """Represents a pre-configured user/principal in the mock Okta."""

    subject: str  # The 'sub' claim (e.g., "user@example.com")
    principal_type: PrincipalType
    groups: list[str] = field(default_factory=list)
    name: str | None = None
    email: str | None = None
    mfa_verified: bool = False
    custom_claims: dict[str, Any] = field(default_factory=dict)

    def to_claims(self) -> dict[str, Any]:
        """Convert user to JWT claims."""
        claims = {
            "sub": self.subject,
            "principal_type": self.principal_type.value,
        }
        if self.groups:
            claims["groups"] = self.groups
        if self.name:
            claims["name"] = self.name
        if self.email:
            claims["email"] = self.email
        if self.mfa_verified:
            claims["amr"] = ["mfa", "pwd"]  # Authentication Methods References
        else:
            claims["amr"] = ["pwd"]
        claims.update(self.custom_claims)
        return claims


@dataclass
class TokenConfig:
    """Configuration for token issuance."""

    default_ttl_seconds: int = 3600  # 1 hour
    ai_agent_max_ttl_seconds: int = 300  # 5 minutes for AI agents
    machine_ttl_seconds: int = 86400  # 24 hours for machine tokens
    clock_skew_seconds: int = 60  # Allow 60 seconds clock skew


class MockOktaProvider:
    """
    A mock Okta OIDC provider that issues cryptographically valid JWTs.

    This provider generates real RSA keys and signs tokens properly, so the
    verification code path is identical to production. The only difference
    is that tokens are issued by this mock instead of real Okta.
    """

    def __init__(
        self,
        issuer: str = "http://localhost:9000/oauth2/default",
        audience: str = "api://hr-ai-platform",
        client_id: str = "mock-client-id",
    ):
        self.issuer = issuer
        self.audience = audience
        self.client_id = client_id
        self.token_config = TokenConfig()

        # Generate RSA key pair for signing
        self._private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        self._public_key = self._private_key.public_key()
        self._kid = f"mock-key-{uuid.uuid4().hex[:8]}"

        # Pre-configured test users
        self._users: dict[str, MockUser] = {}
        self._setup_default_users()

        # Token revocation list (mapping JTI to expiration timestamp)
        self._revoked_tokens: dict[str, int] = {}

        # Issued tokens tracking (for introspection)
        self._issued_tokens: dict[str, dict[str, Any]] = {}

    def _setup_default_users(self) -> None:
        """Set up default test users as specified in policy-schema.md."""
        default_users = [
            MockUser(
                subject="admin@local.test",
                principal_type=PrincipalType.HUMAN,
                groups=["hr-platform-admins"],
                name="Test Admin",
                email="admin@local.test",
                mfa_verified=True,
            ),
            MockUser(
                subject="user@local.test",
                principal_type=PrincipalType.HUMAN,
                groups=["employees"],
                name="Test User",
                email="user@local.test",
            ),
            MockUser(
                subject="svc-workflow@local.test",
                principal_type=PrincipalType.MACHINE,
                groups=[],
                name="Onboarding Workflow Service",
            ),
            MockUser(
                subject="agent-assistant@local.test",
                principal_type=PrincipalType.AI_AGENT,
                groups=[],
                name="HR Assistant Agent",
            ),
            MockUser(
                subject="unauthorized@local.test",
                principal_type=PrincipalType.HUMAN,
                groups=[],
                name="Unauthorized User",
                email="unauthorized@local.test",
            ),
        ]
        for user in default_users:
            self._users[user.subject] = user

    def register_user(self, user: MockUser) -> None:
        """Register a new user/principal for testing."""
        self._users[user.subject] = user

    def get_user(self, subject: str) -> MockUser | None:
        """Get a registered user by subject."""
        return self._users.get(subject)

    def issue_token(
        self,
        subject: str,
        principal_type: PrincipalType | str | None = None,
        groups: list[str] | None = None,
        ttl_seconds: int | None = None,
        additional_claims: dict[str, Any] | None = None,
        token_type: str = "access",
    ) -> str:
        """
        Issue a signed JWT token.

        Args:
            subject: The subject claim (user identifier)
            principal_type: Override the principal type (uses registered user's type if None)
            groups: Override groups (uses registered user's groups if None)
            ttl_seconds: Override TTL (uses default based on principal type if None)
            additional_claims: Extra claims to include in the token
            token_type: "access" or "id"

        Returns:
            Signed JWT string
        """
        now = int(time.time())
        jti = str(uuid.uuid4())

        # Look up registered user or create ad-hoc claims
        user = self._users.get(subject)

        if user:
            claims = user.to_claims()
            effective_principal_type = user.principal_type
        else:
            # Ad-hoc token for unregistered subject
            if principal_type is None:
                principal_type = PrincipalType.HUMAN
            elif isinstance(principal_type, str):
                principal_type = PrincipalType(principal_type)
            effective_principal_type = principal_type
            claims = {
                "sub": subject,
                "principal_type": principal_type.value,
            }

        # Override groups if provided
        if groups is not None:
            claims["groups"] = groups

        # Determine TTL based on principal type
        if ttl_seconds is None:
            if effective_principal_type == PrincipalType.AI_AGENT:
                ttl_seconds = self.token_config.ai_agent_max_ttl_seconds
            elif effective_principal_type == PrincipalType.MACHINE:
                ttl_seconds = self.token_config.machine_ttl_seconds
            else:
                ttl_seconds = self.token_config.default_ttl_seconds

        # Build standard JWT claims
        token_claims = {
            **claims,
            "iss": self.issuer,
            "aud": self.audience,
            "iat": now,
            "exp": now + ttl_seconds,
            "jti": jti,
            "cid": self.client_id,  # Client ID claim (Okta-specific)
        }

        # Add token type specific claims
        if token_type == "id":
            token_claims["nonce"] = str(uuid.uuid4())
            token_claims["auth_time"] = now

        # Merge additional claims
        if additional_claims:
            token_claims.update(additional_claims)

        # Sign the token
        token = jwt.encode(
            token_claims,
            self._private_key,
            algorithm="RS256",
            headers={"kid": self._kid},
        )

        # Track issued token for introspection
        self._issued_tokens[jti] = {
            "claims": token_claims,
            "issued_at": now,
            "expires_at": now + ttl_seconds,
            "token_type": token_type,
        }

        return token

    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token. Returns True if token was valid and is now revoked.
        """
        try:
            # Decode without verification to get JTI and expiration
            unverified = jwt.decode(token, options={"verify_signature": False})
            jti = unverified.get("jti")
            exp = unverified.get("exp")
            if jti and exp:
                self._revoked_tokens[jti] = exp
                return True
        except jwt.DecodeError:
            pass
        return False

    def is_token_revoked(self, token: str) -> bool:
        """Check if a token has been revoked."""
        self._cleanup_revoked_tokens()
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            jti = unverified.get("jti")
            return jti in self._revoked_tokens if jti else False
        except jwt.DecodeError:
            return False

    def _cleanup_revoked_tokens(self) -> None:
        """Remove expired tokens from the revocation list to prevent memory leak."""
        now = int(time.time())
        # We only cleanup every few calls to avoid overhead, or just do it every time if list is small
        # For simplicity in mock, we'll just do it.
        expired = [jti for jti, exp in self._revoked_tokens.items() if exp < now]
        for jti in expired:
            del self._revoked_tokens[jti]

    def verify_token(self, token: str, verify_exp: bool = True) -> dict[str, Any]:
        """
        Verify and decode a token.

        This uses the same verification logic that would be used in production,
        validating signature, issuer, audience, and expiration.

        Args:
            token: The JWT string to verify
            verify_exp: Whether to verify expiration (set False for testing)

        Returns:
            Decoded token claims

        Raises:
            jwt.InvalidTokenError: If token is invalid
        """
        options = {
            "verify_signature": True,
            "verify_exp": verify_exp,
            "verify_iat": True,
            "verify_aud": True,
            "require": ["exp", "iat", "iss", "sub", "aud"],
        }

        claims = jwt.decode(
            token,
            self._public_key,
            algorithms=["RS256"],
            audience=self.audience,
            issuer=self.issuer,
            options=options,
        )

        # Check revocation
        self._cleanup_revoked_tokens()
        if claims.get("jti") in self._revoked_tokens:
            raise jwt.InvalidTokenError("Token has been revoked")

        return claims

    def introspect_token(self, token: str) -> dict[str, Any]:
        """
        Introspect a token (RFC 7662).

        Returns token metadata including active status.
        """
        try:
            claims = self.verify_token(token)
            return {
                "active": True,
                "sub": claims.get("sub"),
                "client_id": claims.get("cid"),
                "username": claims.get("sub"),
                "token_type": "Bearer",
                "exp": claims.get("exp"),
                "iat": claims.get("iat"),
                "iss": claims.get("iss"),
                "aud": claims.get("aud"),
                "principal_type": claims.get("principal_type"),
                "groups": claims.get("groups", []),
            }
        except jwt.InvalidTokenError:
            return {"active": False}

    def get_jwks(self) -> dict[str, Any]:
        """
        Get the JSON Web Key Set (JWKS).

        This returns the public key in JWK format, which clients use to
        verify token signatures.
        """
        # Get public key numbers
        public_numbers = self._public_key.public_numbers()

        # Convert to base64url encoding (without padding)
        def int_to_base64url(n: int, length: int) -> str:
            import base64

            data = n.to_bytes(length, byteorder="big")
            return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

        # RSA public key has n (modulus) and e (exponent)
        n = int_to_base64url(public_numbers.n, 256)  # 2048 bits = 256 bytes
        e = int_to_base64url(public_numbers.e, 3)  # e is typically 65537 (3 bytes)

        return {
            "keys": [
                {
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "kid": self._kid,
                    "n": n,
                    "e": e,
                }
            ]
        }

    def get_openid_configuration(self) -> dict[str, Any]:
        """
        Get the OpenID Connect discovery document.

        This is served at /.well-known/openid-configuration and tells clients
        where to find various OIDC endpoints.
        """
        base_url = self.issuer.rstrip("/")

        return {
            "issuer": self.issuer,
            "authorization_endpoint": f"{base_url}/v1/authorize",
            "token_endpoint": f"{base_url}/v1/token",
            "userinfo_endpoint": f"{base_url}/v1/userinfo",
            "jwks_uri": f"{base_url}/v1/keys",
            "introspection_endpoint": f"{base_url}/v1/introspect",
            "revocation_endpoint": f"{base_url}/v1/revoke",
            "response_types_supported": [
                "code",
                "id_token",
                "token",
                "code id_token",
                "code token",
                "id_token token",
                "code id_token token",
            ],
            "subject_types_supported": ["public"],
            "id_token_signing_alg_values_supported": ["RS256"],
            "scopes_supported": ["openid", "profile", "email", "groups"],
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
                "private_key_jwt",
            ],
            "claims_supported": [
                "sub",
                "name",
                "email",
                "groups",
                "principal_type",
                "iss",
                "aud",
                "exp",
                "iat",
                "jti",
            ],
            "grant_types_supported": [
                "authorization_code",
                "refresh_token",
                "client_credentials",
            ],
        }

    def get_userinfo(self, token: str) -> dict[str, Any]:
        """
        Get userinfo for a token (OIDC userinfo endpoint).
        """
        claims = self.verify_token(token)
        subject = claims.get("sub")
        user = self._users.get(subject)

        userinfo = {"sub": subject}
        if user:
            if user.name:
                userinfo["name"] = user.name
            if user.email:
                userinfo["email"] = user.email
                userinfo["email_verified"] = True
            if user.groups:
                userinfo["groups"] = user.groups
            userinfo["principal_type"] = user.principal_type.value
        else:
            userinfo.update(
                {k: v for k, v in claims.items() if k not in ["iss", "aud", "exp", "iat", "jti"]}
            )

        return userinfo


# ---------------------------------------------------------------------------
# FastAPI Server Implementation
# ---------------------------------------------------------------------------


def create_mock_okta_app(provider: MockOktaProvider | None = None):
    """
    Create a FastAPI application that serves as a mock Okta OIDC provider.

    This can be run standalone or mounted as a sub-application for testing.
    """
    from fastapi import FastAPI, HTTPException, Header, Form, Request
    from fastapi.responses import JSONResponse

    if provider is None:
        provider = MockOktaProvider()

    app = FastAPI(
        title="Mock Okta OIDC Provider",
        description="A mock Okta server for local development and testing",
        version="1.0.0",
    )

    # Store provider on app for access in tests
    app.state.provider = provider

    @app.get("/.well-known/openid-configuration")
    async def openid_configuration():
        """OIDC Discovery endpoint."""
        return provider.get_openid_configuration()

    @app.get("/oauth2/default/.well-known/openid-configuration")
    async def openid_configuration_alt():
        """Alternative OIDC Discovery endpoint path."""
        return provider.get_openid_configuration()

    @app.get("/oauth2/default/v1/keys")
    @app.get("/oauth2/v1/keys")
    async def jwks():
        """JWKS endpoint - returns public keys for token verification."""
        return provider.get_jwks()

    @app.post("/oauth2/default/v1/token")
    @app.post("/oauth2/v1/token")
    async def token(
        grant_type: str = Form(...),
        client_id: str = Form(None),
        client_secret: str = Form(None),
        username: str = Form(None),
        password: str = Form(None),
        scope: str = Form("openid"),
    ):
        """
        Token endpoint - issues tokens.

        Supports:
        - client_credentials: For machine/service accounts
        - password: For testing user authentication (NOT for production!)
        """
        if grant_type == "client_credentials":
            # Machine token - use client_id as subject
            if not client_id:
                raise HTTPException(status_code=400, detail="client_id required")

            # Look up as machine user or create ad-hoc
            user = provider.get_user(client_id)
            if user:
                token = provider.issue_token(subject=client_id)
            else:
                token = provider.issue_token(
                    subject=client_id,
                    principal_type=PrincipalType.MACHINE,
                )

            return {
                "access_token": token,
                "token_type": "Bearer",
                "expires_in": provider.token_config.machine_ttl_seconds,
                "scope": scope,
            }

        elif grant_type == "password":
            # Resource Owner Password grant (for testing only)
            if not username:
                raise HTTPException(status_code=400, detail="username required")

            # In mock mode, any password works for registered users
            user = provider.get_user(username)
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail="invalid_grant",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token = provider.issue_token(subject=username)
            id_token = provider.issue_token(subject=username, token_type="id")

            ttl = (
                provider.token_config.ai_agent_max_ttl_seconds
                if user.principal_type == PrincipalType.AI_AGENT
                else provider.token_config.default_ttl_seconds
            )

            return {
                "access_token": access_token,
                "id_token": id_token,
                "token_type": "Bearer",
                "expires_in": ttl,
                "scope": scope,
            }

        else:
            raise HTTPException(
                status_code=400,
                detail=f"unsupported_grant_type: {grant_type}",
            )

    @app.post("/oauth2/default/v1/introspect")
    @app.post("/oauth2/v1/introspect")
    async def introspect(
        token: str = Form(...),
        token_type_hint: str = Form(None),
    ):
        """Token introspection endpoint (RFC 7662)."""
        return provider.introspect_token(token)

    @app.post("/oauth2/default/v1/revoke")
    @app.post("/oauth2/v1/revoke")
    async def revoke(
        token: str = Form(...),
        token_type_hint: str = Form(None),
    ):
        """Token revocation endpoint (RFC 7009)."""
        provider.revoke_token(token)
        # RFC 7009 says always return 200
        return JSONResponse(status_code=200, content={})

    @app.get("/oauth2/default/v1/userinfo")
    @app.get("/oauth2/v1/userinfo")
    async def userinfo(authorization: str = Header(...)):
        """Userinfo endpoint - returns user claims."""
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401,
                detail="invalid_token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:]  # Strip "Bearer "
        try:
            return provider.get_userinfo(token)
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=401,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )

    # ---------------------------------------------------------------------------
    # Test/Admin endpoints (not part of OIDC spec, but useful for testing)
    # ---------------------------------------------------------------------------

    @app.post("/test/users")
    async def create_test_user(request_data: CreateUserRequest):
        """Create a test user (admin endpoint for testing)."""
        user = MockUser(
            subject=request_data.subject,
            principal_type=PrincipalType(request_data.principal_type),
            groups=request_data.groups,
            name=request_data.name,
            email=request_data.email,
            mfa_verified=request_data.mfa_verified,
            custom_claims=request_data.custom_claims,
        )
        provider.register_user(user)
        return {"status": "created", "subject": user.subject}

    @app.get("/test/users/{subject}")
    async def get_test_user(subject: str):
        """Get a test user (admin endpoint for testing)."""
        user = provider.get_user(subject)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "subject": user.subject,
            "principal_type": user.principal_type.value,
            "groups": user.groups,
            "name": user.name,
            "email": user.email,
        }

    @app.post("/test/tokens")
    async def create_test_token(request_data: CreateTokenRequest):
        """
        Create a token directly (bypassing OAuth flows).

        Useful for test setup where you need a specific token configuration.
        """
        token = provider.issue_token(
            subject=request_data.subject,
            principal_type=request_data.principal_type,
            groups=request_data.groups,
            ttl_seconds=request_data.ttl_seconds,
            additional_claims=request_data.additional_claims,
        )
        return {"access_token": token, "token_type": "Bearer"}

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "issuer": provider.issuer}

    return app


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(description="Run Mock Okta OIDC Provider")
    parser.add_argument("--port", type=int, default=9000, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    # Create provider with issuer matching the server URL
    issuer = f"http://{args.host}:{args.port}/oauth2/default"
    provider = MockOktaProvider(issuer=issuer)
    app = create_mock_okta_app(provider)

    print(f"Starting Mock Okta OIDC Provider")
    print(f"  Issuer: {issuer}")
    print(f"  Discovery: http://{args.host}:{args.port}/.well-known/openid-configuration")
    print(f"  JWKS: http://{args.host}:{args.port}/oauth2/v1/keys")
    print(f"\nPre-configured test users:")
    for subject, user in provider._users.items():
        print(f"  - {subject} ({user.principal_type.value})")

    uvicorn.run(app, host=args.host, port=args.port)
