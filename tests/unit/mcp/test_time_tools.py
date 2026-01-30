import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.time import request_time_off

@pytest.mark.asyncio
@patch("src.mcp.tools.time.backend_client.call_action")
async def test_request_time_off_auto_id(mock_call):
    """Verify tool auto-generates a transaction ID if missing."""
    mock_call.return_value = {"data": {"request_id": "TOR-123"}}
    
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": "Bearer fake"}}
    
    await request_time_off(
        mock_ctx, 
        employee_id="EMP001", 
        type="PTO", 
        start_date="2026-06-01", 
        end_date="2026-06-05", 
        hours=40
    )
    
    # Check that call_action was called with an auto-generated transaction_id in params
    args, kwargs = mock_call.call_args
    params = args[2] if len(args) > 2 else kwargs.get("parameters", {})
    assert "transaction_id" in params
    assert params["transaction_id"].startswith("TXN-")
