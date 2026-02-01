import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
@patch("src.mcp.tools.payroll.get_mcp_token")
async def test_payroll_mfa_enforcement(mock_mcp_token):
    """Verify Payroll tools enforce MFA at MCP layer for ADMINs."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    # 1. No MFA token (but is an ADMIN)

    token_payload = {
        "sub": "ADM001", 
        "principal_type": "HUMAN", 
        "groups": ["hr-platform-admins"],
        "amr": ["pwd"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    from src.mcp.tools.payroll import get_compensation
    result = await get_compensation(mock_ctx, "EMP001")
    assert "MFA_REQUIRED" in result

    # 2. MFA token + ADMIN
    token_payload["amr"] = ["mfa", "pwd"]
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    with patch("src.mcp.tools.payroll.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"data": {"compensation": {"total": 100000}}}
        result = await get_compensation(mock_ctx, "EMP001")
        assert "100000" in result
        mock_call.assert_called_once()