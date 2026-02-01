import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.payroll import get_compensation

@pytest.mark.asyncio
@patch("src.mcp.tools.payroll.backend_client.call_action")
@patch("src.mcp.tools.payroll.get_mcp_token")
async def test_get_compensation_mfa_missing(mock_mcp_token, mock_call):
    """Verify tool returns error if token lacks MFA claim (even for ADMIN)."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    # Principal WITH ADMIN group but WITHOUT MFA

    token_payload = {
        "sub": "EMP001", 
        "principal_type": "HUMAN", 
        "groups": ["hr-platform-admins"],
        "amr": ["pwd"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    result = await get_compensation(mock_ctx, "EMP001")
    
    assert "MFA_REQUIRED" in result
    mock_call.assert_not_called()

@pytest.mark.asyncio
@patch("src.mcp.tools.payroll.backend_client.call_action")
@patch("src.mcp.tools.payroll.get_mcp_token")
async def test_get_compensation_mfa_present(mock_mcp_token, mock_call):
    """Verify tool calls backend if token HAS MFA claim and ADMIN role."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    # Principal WITH ADMIN group and WITH MFA

    token_payload = {
        "sub": "EMP001", 
        "principal_type": "HUMAN", 
        "groups": ["hr-platform-admins"],
        "amr": ["mfa", "pwd"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    mock_call.return_value = {"data": {"employee_id": "EMP001", "compensation": {}}}
    
    result = await get_compensation(mock_ctx, "EMP001")
    
    assert "EMP001" in result
    mock_call.assert_called_once()