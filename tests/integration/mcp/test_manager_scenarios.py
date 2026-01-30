import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_manager_approve_flow():
    """Verify manager can list reports and approve requests."""
    token_payload = {"sub": "MGR001", "principal_type": "HUMAN"}
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
    
    with patch("src.mcp.tools.hcm.backend_client.call_action", new_callable=AsyncMock) as mock_hcm_call, \
         patch("src.mcp.tools.time.backend_client.call_action", new_callable=AsyncMock) as mock_time_call:
        
        # 1. List reports
        mock_hcm_call.return_value = {"data": {"direct_reports": [{"employee_id": "EMP001"}]}}
        from src.mcp.tools.hcm import list_direct_reports
        reports = await list_direct_reports(mock_ctx, "MGR001")
        assert "EMP001" in reports
        
        # 2. Approve request
        mock_time_call.return_value = {"data": {"status": "APPROVED"}}
        from src.mcp.tools.time import approve_time_off
        result = await approve_time_off(mock_ctx, "TOR-123")
        assert "APPROVED" in result
