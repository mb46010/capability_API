import pytest
import jwt
from unittest.mock import patch
from src.adapters.auth import MockOktaProvider, MockTokenVerifier

@pytest.fixture(autouse=True)
def mock_mcp_auth_verifier():
    """
    Autouse fixture that patches the MCP auth verifier to use a mock provider.
    This ensures that integration tests using jwt.encode with 'secret' still work
    by bypassing the real JWKS/RSA verification, OR we can use it to provide
    a consistent provider for tests that want to use real signatures.
    """
    provider = MockOktaProvider()
    verifier = MockTokenVerifier(provider)
    
    with patch("src.mcp.adapters.auth.get_verifier", return_value=verifier):
        yield provider

@pytest.fixture
def issue_token(mock_mcp_auth_verifier):
    """Helper to issue valid tokens for tests."""
    def _issue(subject, principal_type="HUMAN", groups=None, additional_claims=None):
        return mock_mcp_auth_verifier.issue_token(
            subject=subject,
            principal_type=principal_type,
            groups=groups or [],
            additional_claims=additional_claims or {}
        )
    return _issue
