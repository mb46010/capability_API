"""
Tests for Mock Okta OIDC Provider and Token Verifier

These tests verify:
1. Token issuance with correct claims
2. Token signature verification
3. Principal type handling (HUMAN, MACHINE, AI_AGENT)
4. TTL enforcement (especially for AI agents)
5. Token revocation
6. OIDC discovery endpoints
7. Error handling
"""

import time
import pytest
import jwt
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, "/home/claude/hr-ai-platform")

from src.adapters.auth import (
    MockOktaProvider,
    MockUser,
    PrincipalType,
    MockTokenVerifier,
    TokenVerificationError,
    VerifiedPrincipal,
    create_mock_okta_app,
    AuthConfig,
    create_token_verifier,
)
from src.lib.config_validator import settings


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider():
    """Create a fresh MockOktaProvider for each test."""
    return MockOktaProvider(
        issuer="http://test.local/oauth2/default",
        audience="api://test",
    )


@pytest.fixture
def verifier(provider):
    """Create a MockTokenVerifier using the provider."""
    return MockTokenVerifier(provider)


@pytest.fixture
def app(provider):
    """Create a FastAPI test client for the mock Okta server."""
    return TestClient(create_mock_okta_app(provider))


# ---------------------------------------------------------------------------
# Token Issuance Tests
# ---------------------------------------------------------------------------


class TestTokenIssuance:
    """Tests for token issuance."""

    def test_issue_token_for_registered_user(self, provider):
        """Token for registered user includes correct claims."""
        token = provider.issue_token(subject="admin@local.test")

        # Decode without verification to inspect claims
        claims = jwt.decode(token, options={"verify_signature": False})

        assert claims["sub"] == "admin@local.test"
        assert claims["principal_type"] == "HUMAN"
        assert claims["groups"] == ["hr-platform-admins"]
        assert claims["iss"] == "http://test.local/oauth2/default"
        assert claims["aud"] == "api://test"
        assert "exp" in claims
        assert "iat" in claims
        assert "jti" in claims

    def test_issue_token_for_unregistered_user(self, provider):
        """Token for unregistered user uses provided principal type."""
        token = provider.issue_token(
            subject="new-user@example.com",
            principal_type=PrincipalType.HUMAN,
            groups=["custom-group"],
        )

        claims = jwt.decode(token, options={"verify_signature": False})

        assert claims["sub"] == "new-user@example.com"
        assert claims["principal_type"] == "HUMAN"
        assert claims["groups"] == ["custom-group"]

    def test_ai_agent_short_ttl(self, provider):
        """AI agent tokens have short TTL by default."""
        token = provider.issue_token(subject="agent-assistant@local.test")
        claims = jwt.decode(token, options={"verify_signature": False})

        ttl = claims["exp"] - claims["iat"]
        assert ttl == 300  # 5 minutes for AI agents

    def test_machine_long_ttl(self, provider):
        """Machine tokens have longer TTL by default."""
        token = provider.issue_token(subject="svc-workflow@local.test")
        claims = jwt.decode(token, options={"verify_signature": False})

        ttl = claims["exp"] - claims["iat"]
        assert ttl == 86400  # 24 hours for machines

    def test_human_default_ttl(self, provider):
        """Human tokens have standard TTL by default."""
        token = provider.issue_token(subject="user@local.test")
        claims = jwt.decode(token, options={"verify_signature": False})

        ttl = claims["exp"] - claims["iat"]
        assert ttl == 3600  # 1 hour for humans

    def test_custom_ttl_override(self, provider):
        """TTL can be overridden."""
        token = provider.issue_token(
            subject="admin@local.test",
            ttl_seconds=120,
        )
        claims = jwt.decode(token, options={"verify_signature": False})

        ttl = claims["exp"] - claims["iat"]
        assert ttl == 120

    def test_additional_claims(self, provider):
        """Additional claims are included in token."""
        token = provider.issue_token(
            subject="admin@local.test",
            additional_claims={"custom_claim": "custom_value", "department": "HR"},
        )
        claims = jwt.decode(token, options={"verify_signature": False})

        assert claims["custom_claim"] == "custom_value"
        assert claims["department"] == "HR"

    def test_mfa_in_amr_claim(self, provider):
        """MFA status is reflected in AMR claim."""
        # Admin has MFA verified
        token = provider.issue_token(subject="admin@local.test")
        claims = jwt.decode(token, options={"verify_signature": False})
        assert "mfa" in claims["amr"]

        # Regular user does not
        token = provider.issue_token(subject="user@local.test")
        claims = jwt.decode(token, options={"verify_signature": False})
        assert "mfa" not in claims["amr"]


# ---------------------------------------------------------------------------
# Token Verification Tests
# ---------------------------------------------------------------------------


class TestTokenVerification:
    """Tests for token verification."""

    def test_verify_valid_token(self, provider, verifier):
        """Valid token verifies successfully."""
        token = provider.issue_token(subject="admin@local.test")
        principal = verifier.verify(token)

        assert principal.subject == "admin@local.test"
        assert principal.principal_type == PrincipalType.HUMAN
        assert principal.groups == ["hr-platform-admins"]
        assert principal.mfa_verified is True

    def test_verify_expired_token(self, provider, verifier):
        """Expired token raises error."""
        token = provider.issue_token(
            subject="admin@local.test",
            ttl_seconds=-10,  # Already expired
        )

        with pytest.raises(TokenVerificationError) as exc_info:
            verifier.verify(token)

        assert exc_info.value.error_code == "token_expired"

    def test_verify_tampered_token(self, provider, verifier):
        """Tampered token raises error."""
        token = provider.issue_token(subject="admin@local.test")

        # Tamper with the token payload
        parts = token.split(".")
        parts[1] = parts[1][:-4] + "XXXX"  # Corrupt payload
        tampered_token = ".".join(parts)

        with pytest.raises(TokenVerificationError):
            verifier.verify(tampered_token)

    def test_verify_wrong_issuer(self, provider, verifier):
        """Token with wrong issuer claim fails verification.
        
        Note: In practice, tokens from a different issuer would have different
        signing keys, so signature verification fails first. This test verifies
        that behavior - we can't verify tokens we didn't issue.
        """
        # Create a second provider with different issuer (and different keys)
        other_provider = MockOktaProvider(
            issuer="http://other.local/oauth2/default",
            audience="api://test",
        )
        token = other_provider.issue_token(subject="admin@local.test")

        # Try to verify with original provider's verifier
        # This should fail because the signing keys don't match
        with pytest.raises(TokenVerificationError):
            verifier.verify(token)

    def test_verify_wrong_audience(self, provider, verifier):
        """Token with wrong audience claim fails verification.
        
        Note: Like wrong issuer, different providers have different keys.
        """
        # Create provider with different audience (and different keys)
        other_provider = MockOktaProvider(
            issuer="http://test.local/oauth2/default",
            audience="api://other",
        )
        token = other_provider.issue_token(subject="admin@local.test")

        # Try to verify with original provider's verifier
        with pytest.raises(TokenVerificationError):
            verifier.verify(token)


# ---------------------------------------------------------------------------
# Token Revocation Tests
# ---------------------------------------------------------------------------


class TestTokenRevocation:
    """Tests for token revocation."""

    def test_revoke_token(self, provider, verifier):
        """Revoked token fails verification."""
        token = provider.issue_token(subject="admin@local.test")

        # Token is valid before revocation
        principal = verifier.verify(token)
        assert principal.subject == "admin@local.test"

        # Revoke the token
        assert provider.revoke_token(token) is True

        # Token is now invalid
        with pytest.raises(TokenVerificationError):
            verifier.verify(token)

    def test_is_token_revoked(self, provider):
        """is_token_revoked correctly reports status."""
        token = provider.issue_token(subject="admin@local.test")

        assert provider.is_token_revoked(token) is False
        provider.revoke_token(token)
        assert provider.is_token_revoked(token) is True


# ---------------------------------------------------------------------------
# VerifiedPrincipal Tests
# ---------------------------------------------------------------------------


class TestVerifiedPrincipal:
    """Tests for VerifiedPrincipal domain object."""

    def test_principal_type_helpers(self, provider, verifier):
        """Principal type helper properties work correctly."""
        # Human
        token = provider.issue_token(subject="admin@local.test")
        principal = verifier.verify(token)
        assert principal.is_human is True
        assert principal.is_machine is False
        assert principal.is_ai_agent is False

        # Machine
        token = provider.issue_token(subject="svc-workflow@local.test")
        principal = verifier.verify(token)
        assert principal.is_human is False
        assert principal.is_machine is True
        assert principal.is_ai_agent is False

        # AI Agent
        token = provider.issue_token(subject="agent-assistant@local.test")
        principal = verifier.verify(token)
        assert principal.is_human is False
        assert principal.is_machine is False
        assert principal.is_ai_agent is True

    def test_has_group(self, provider, verifier):
        """has_group correctly checks group membership."""
        token = provider.issue_token(subject="admin@local.test")
        principal = verifier.verify(token)

        assert principal.has_group("hr-platform-admins") is True
        assert principal.has_group("employees") is False

    def test_time_until_expiry(self, provider, verifier):
        """time_until_expiry returns correct value."""
        token = provider.issue_token(subject="admin@local.test", ttl_seconds=3600)
        principal = verifier.verify(token)

        # Should be close to 3600 (minus small time delta for test execution)
        assert 3595 < principal.time_until_expiry() <= 3600


# ---------------------------------------------------------------------------
# OIDC Endpoint Tests
# ---------------------------------------------------------------------------


class TestOIDCEndpoints:
    """Tests for OIDC discovery endpoints."""

    def test_openid_configuration(self, app, provider):
        """Discovery endpoint returns valid configuration."""
        response = app.get("/.well-known/openid-configuration")
        assert response.status_code == 200

        config = response.json()
        assert config["issuer"] == provider.issuer
        assert "jwks_uri" in config
        assert "token_endpoint" in config
        assert "introspection_endpoint" in config

    def test_jwks_endpoint(self, app):
        """JWKS endpoint returns valid keys."""
        response = app.get("/oauth2/v1/keys")
        assert response.status_code == 200

        jwks = response.json()
        assert "keys" in jwks
        assert len(jwks["keys"]) == 1

        key = jwks["keys"][0]
        assert key["kty"] == "RSA"
        assert key["alg"] == "RS256"
        assert key["use"] == "sig"
        assert "kid" in key
        assert "n" in key
        assert "e" in key

    def test_token_endpoint_client_credentials(self, app):
        """Token endpoint issues tokens for client_credentials grant."""
        response = app.post(
            "/oauth2/v1/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "svc-workflow@local.test",
                "client_secret": "not-checked-in-mock",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "Bearer"

    def test_token_endpoint_password_grant(self, app):
        """Token endpoint issues tokens for password grant (test only)."""
        response = app.post(
            "/oauth2/v1/token",
            data={
                "grant_type": "password",
                "username": "admin@local.test",
                "password": "any-password-works",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert "id_token" in data

    def test_token_endpoint_unknown_user(self, app):
        """Token endpoint rejects unknown users."""
        response = app.post(
            "/oauth2/v1/token",
            data={
                "grant_type": "password",
                "username": "unknown@example.com",
                "password": "any",
            },
        )
        assert response.status_code == 401

    def test_introspect_endpoint(self, app, provider):
        """Introspection endpoint returns token details."""
        token = provider.issue_token(subject="admin@local.test")

        response = app.post(
            "/oauth2/v1/introspect",
            data={"token": token},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["active"] is True
        assert data["sub"] == "admin@local.test"
        assert data["principal_type"] == "HUMAN"

    def test_introspect_invalid_token(self, app):
        """Introspection returns inactive for invalid tokens."""
        response = app.post(
            "/oauth2/v1/introspect",
            data={"token": "invalid-token"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["active"] is False

    def test_revoke_endpoint(self, app, provider, verifier):
        """Revocation endpoint revokes tokens."""
        token = provider.issue_token(subject="admin@local.test")

        # Verify token works
        principal = verifier.verify(token)
        assert principal.subject == "admin@local.test"

        # Revoke via endpoint
        response = app.post(
            "/oauth2/v1/revoke",
            data={"token": token},
        )
        assert response.status_code == 200

        # Token should now be invalid
        with pytest.raises(TokenVerificationError):
            verifier.verify(token)

    def test_userinfo_endpoint(self, app, provider):
        """Userinfo endpoint returns user claims."""
        token = provider.issue_token(subject="admin@local.test")

        response = app.get(
            "/oauth2/v1/userinfo",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

        data = response.json()
        assert data["sub"] == "admin@local.test"
        assert data["name"] == "Test Admin"
        assert data["email"] == "admin@local.test"
        assert data["groups"] == ["hr-platform-admins"]


# ---------------------------------------------------------------------------
# Test Admin Endpoints
# ---------------------------------------------------------------------------


class TestAdminEndpoints:
    """Tests for test/admin endpoints."""

    @pytest.fixture
    def auth_headers(self):
        return {"X-Test-Secret": settings.MOCK_OKTA_TEST_SECRET}

    def test_unauthorized_access(self, app):
        """Endpoints are protected without secret."""
        response = app.post("/test/users", json={"subject": "test"})
        assert response.status_code == 403
        
        response = app.get("/test/users/admin@local.test")
        assert response.status_code == 403
        
        response = app.post("/test/tokens", json={"subject": "test"})
        assert response.status_code == 403

    def test_create_user(self, app, verifier, auth_headers):
        """Can create new test users via API."""
        response = app.post(
            "/test/users",
            json={
                "subject": "new-test-user@example.com",
                "principal_type": "HUMAN",
                "groups": ["test-group"],
                "name": "New Test User",
                "email": "new-test-user@example.com",
            },
            headers=auth_headers
        )
        assert response.status_code == 200

        # Can now get token for this user
        response = app.post(
            "/test/tokens",
            json={"subject": "new-test-user@example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200

        token = response.json()["access_token"]
        principal = verifier.verify(token)
        assert principal.subject == "new-test-user@example.com"
        assert principal.has_group("test-group")

    def test_get_user(self, app, auth_headers):
        """Can retrieve user details."""
        response = app.get("/test/users/admin@local.test", headers=auth_headers)
        assert response.status_code == 200

        data = response.json()
        assert data["subject"] == "admin@local.test"
        assert data["principal_type"] == "HUMAN"

    def test_get_nonexistent_user(self, app, auth_headers):
        """404 for nonexistent user."""
        response = app.get("/test/users/nonexistent@example.com", headers=auth_headers)
        assert response.status_code == 404

    def test_create_token_directly(self, app, verifier, auth_headers):
        """Can create tokens with custom claims."""
        response = app.post(
            "/test/tokens",
            json={
                "subject": "admin@local.test",
                "ttl_seconds": 60,
                "additional_claims": {"custom": "value"},
            },
            headers=auth_headers
        )
        assert response.status_code == 200

        token = response.json()["access_token"]
        claims = jwt.decode(token, options={"verify_signature": False})
        assert claims["custom"] == "value"
        assert claims["exp"] - claims["iat"] == 60


# ---------------------------------------------------------------------------
# Factory Tests
# ---------------------------------------------------------------------------


class TestFactory:
    """Tests for verifier factory."""

    def test_create_mock_verifier(self):
        """Factory creates mock verifier."""
        config = AuthConfig.for_local_development()
        verifier = create_token_verifier(config)

        assert isinstance(verifier, MockTokenVerifier)

    def test_config_for_local_development(self):
        """Local development config has correct defaults."""
        config = AuthConfig.for_local_development()

        assert config.mode == "mock"
        assert "localhost" in config.issuer
        assert config.audience == "api://hr-ai-platform"

    def test_config_for_production(self):
        """Production config stores provided values."""
        config = AuthConfig.for_production(
            issuer="https://example.okta.com/oauth2/default",
            audience="api://prod",
            client_id="prod-client-id",
        )

        assert config.mode == "okta"
        assert config.issuer == "https://example.okta.com/oauth2/default"
        assert config.audience == "api://prod"
        assert config.client_id == "prod-client-id"


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
