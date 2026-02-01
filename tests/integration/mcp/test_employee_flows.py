import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.adapters.auth import PrincipalContext

@pytest.mark.asyncio
@patch("src.mcp.tools.time.get_mcp_token")
async def test_employee_request_time_off_success(mock_mcp_token):
    """Verify an employee can request time off and see balance."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    token_payload = {

        "sub": "EMP001", 
        "principal_type": "HUMAN",
        "groups": ["employees"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    with patch("src.mcp.tools.time.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {"data": {"request_id": "TOR-999", "status": "PENDING"}}
        
        from src.mcp.tools.time import request_time_off
        result = await request_time_off(
            mock_ctx, 
            employee_id="EMP001", 
            type="PTO", 
            start_date="2026-10-01", 
            end_date="2026-10-05", 
            hours=40
        )
        
        assert "TOR-999" in result
        assert "PENDING" in result
        mock_call.assert_called_once()

@pytest.mark.asyncio
@patch("src.mcp.tools.time.get_mcp_token")
async def test_employee_get_balance(mock_mcp_token):
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    token_payload = {

        "sub": "EMP001", 
        "principal_type": "HUMAN",
        "groups": ["employees"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    with patch("src.mcp.tools.time.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = {
            "data": {
                "balances": [{"type": "PTO", "available_hours": 120, "pending_hours": 0}]
            }
        }
        
        from src.mcp.tools.time import get_pto_balance
        result = await get_pto_balance(mock_ctx, "EMP001")
        
        assert "120" in result
        assert "PTO" in result
        mock_call.assert_called_once()