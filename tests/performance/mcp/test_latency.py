import pytest
import time
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

@pytest.mark.asyncio
async def test_mcp_latency_target():
    """Verify MCP overhead is < 100ms (SC-004)."""
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": "Bearer fake"}}
    
    # Mock backend, auth and token exchange to be near-instant
    with patch("src.mcp.lib.decorators.backend_client.call_action", new_callable=AsyncMock) as mock_call, \
         patch("src.mcp.lib.decorators.authenticate_and_authorize", new_callable=AsyncMock) as mock_auth, \
         patch("src.mcp.lib.decorators.get_mcp_token", new_callable=AsyncMock) as mock_token:
        
        mock_auth.return_value = ("fake_token", MagicMock(subject="test"), None)
        mock_token.return_value = "mcp_token"
        mock_call.return_value = {"data": {}}
        
        start_time = time.time()
        from src.mcp.tools.hcm import get_employee
        await get_employee(mock_ctx, "EMP001")
        duration_ms = (time.time() - start_time) * 1000
        
        print(f"MCP Tool Latency: {duration_ms:.2f}ms")
        assert duration_ms < 100, f"MCP latency {duration_ms}ms exceeds 100ms target"
