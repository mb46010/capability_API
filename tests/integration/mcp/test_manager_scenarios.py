import pytest
import jwt
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.hcm import list_direct_reports
from src.mcp.tools.time import approve_time_off

@pytest.mark.asyncio
@patch("src.mcp.lib.decorators.get_mcp_token")
async def test_manager_approve_flow(mock_mcp_token, issue_token):
    """Verify manager can list reports and approve requests."""
    # Mock token exchange
    mock_mcp_token.side_effect = lambda t: f"mcp-{t}"
    
    token = issue_token(
        subject="MGR001",
        principal_type="HUMAN",
        groups=["hr-platform-admins"]
    )
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    # Patch the singleton once
    with patch("src.mcp.adapters.backend.backend_client.call_action") as mock_call:
        
        async def side_effect(domain, action, parameters, token):
            if action == "list_direct_reports":
                return {"data": {"direct_reports": [{"employee_id": "EMP001"}]}}
            elif action == "approve":
                return {"data": {"status": "APPROVED"}}
            return {"data": {}}

        mock_call.side_effect = side_effect
        
        # 1. List reports
        reports = await list_direct_reports(mock_ctx, "MGR001")
        assert "EMP001" in reports
        
        # 2. Approve request
        result = await approve_time_off(mock_ctx, "TOR-123")
        assert "APPROVED" in result
