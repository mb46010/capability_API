import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
@patch("src.mcp.lib.decorators.get_mcp_token")
async def test_payroll_mfa_enforcement(mock_mcp_token, issue_token):
    """Verify Payroll tools enforce MFA at MCP layer for ADMINs."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    # 1. No MFA token (but is an ADMIN)
    token = issue_token(
        subject="ADM001", 
        principal_type="HUMAN", 
        groups=["hr-platform-admins"],
        additional_claims={"amr": ["pwd"]}
    )
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    from src.mcp.tools.payroll import get_compensation
    result = await get_compensation(mock_ctx, "EMP001")
    assert "MFA_REQUIRED" in result

    # 2. MFA token + ADMIN
    token = issue_token(
        subject="ADM001", 
        principal_type="HUMAN", 
        groups=["hr-platform-admins"],
        additional_claims={"amr": ["mfa", "pwd"]}
    )
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    with patch("src.mcp.lib.decorators.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"data": {"compensation": {"total": 100000}}}
        result = await get_compensation(mock_ctx, "EMP001")
        assert "100000" in result
        mock_call.assert_called_once()

@pytest.mark.asyncio
async def test_mcp_rejects_forged_token():
    """Verify MCP server rejects tokens with invalid signatures."""
    # Create a forged token (signed with HS256 and 'fake-secret')
    token_payload = {
        "sub": "attacker", 
        "groups": ["hr-platform-admins"], 
        "principal_type": "HUMAN", 
        "exp": 9999999999,
        "iss": "http://localhost:9000/oauth2/default",
        "aud": "api://hr-ai-platform",
    }
    token = jwt.encode(token_payload, "fake-secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    from src.mcp.tools.payroll import get_compensation
    result = await get_compensation(mock_ctx, "EMP001")
    
    assert "UNAUTHORIZED" in result
    assert "Invalid or malformed token" in result