import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.hcm import list_direct_reports

@pytest.mark.asyncio
@patch("src.mcp.tools.hcm.backend_client.call_action")
async def test_list_direct_reports_success(mock_call):
    # 1. Create a valid mock token for an ADMIN
    token_payload = {
        "sub": "MGR001",
        "principal_type": "HUMAN",
        "groups": ["hr-platform-admins"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")

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