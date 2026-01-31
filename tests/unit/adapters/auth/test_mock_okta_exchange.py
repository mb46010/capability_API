import pytest
import jwt
from unittest.mock import MagicMock
from src.adapters.auth.mock_okta import MockOktaProvider, PrincipalType

@pytest.fixture
def provider():
    return MockOktaProvider()

def test_exchange_token_success(provider):
    """T004: Verify successful token exchange with correct claims."""
    # 1. Issue a valid user token
    user_token = provider.issue_token("EMP001", ttl_seconds=3600)
    user_claims = jwt.decode(user_token, options={"verify_signature": False})
    
    # 2. Exchange it
    exchanged_token = provider.exchange_token(user_token, scope="mcp:use")
    mcp_claims = jwt.decode(exchanged_token, options={"verify_signature": False})
    
    # 3. Verify assertions
    assert (mcp_claims["exp"] - mcp_claims["iat"]) <= 300  # 5 min TTL
    assert mcp_claims["sub"] == "EMP001"
    assert "mcp:use" in mcp_claims["scope"]
    assert mcp_claims["acting_as"] == "mcp-server"
    assert mcp_claims["original_token_id"] == user_claims["jti"]
    assert mcp_claims["auth_time"] == user_claims.get("auth_time", user_claims["iat"])

def test_exchange_token_rejects_nested(provider):
    """T005: Verify chain-of-chains is rejected."""
    # 1. Issue first level user token
    user_token = provider.issue_token("EMP001")
    
    # 2. Exchange for MCP token
    mcp_token_1 = provider.exchange_token(user_token, scope="mcp:use")
    
    # 3. Attempt to exchange the MCP token again -> Should fail
    with pytest.raises(ValueError, match="Subject token is already an exchanged token"):
        provider.exchange_token(mcp_token_1, scope="mcp:use")

def test_exchange_token_missing_authtime(provider):
    """T006: Verify fallback to iat if auth_time is missing."""
    # 1. Issue token WITHOUT auth_time (default for access tokens in mock)
    user_token = provider.issue_token("EMP001", token_type="access")
    user_claims = jwt.decode(user_token, options={"verify_signature": False})
    assert "auth_time" not in user_claims
    
    # 2. Exchange it
    exchanged_token = provider.exchange_token(user_token, scope="mcp:use")
    mcp_claims = jwt.decode(exchanged_token, options={"verify_signature": False})
    
    # 3. Verify auth_time was backfilled from iat
    assert mcp_claims["auth_time"] == user_claims["iat"]
