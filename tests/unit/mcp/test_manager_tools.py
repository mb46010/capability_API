import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.hcm import list_direct_reports

@pytest.mark.asyncio
@patch("src.mcp.lib.decorators.backend_client.call_action")
@patch("src.mcp.lib.decorators.get_mcp_token")
async def test_list_direct_reports_success(mock_mcp_token, mock_call, issue_token):
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    # 1. Create a valid mock token for an ADMIN
    token = issue_token(subject="MGR001", principal_type="HUMAN", groups=["hr-platform-admins"])

    mock_call.return_value = {
        "data": {
            "manager_id": "MGR001",
            "direct_reports": [{"employee_id": "EMP001", "display_name": "John Doe"}]
        }
    }
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    result = await list_direct_reports(mock_ctx, manager_id="MGR001")
    
    assert "MGR001" in result
    assert "John Doe" in result
    mock_call.assert_called_once()