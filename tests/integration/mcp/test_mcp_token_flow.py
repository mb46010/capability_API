import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastmcp import Context
from src.mcp.adapters.auth import get_mcp_token
from src.mcp.tools import hcm
from src.mcp.lib.config import settings

@pytest.fixture
def mock_httpx_client():
    with patch("httpx.AsyncClient") as mock:
        yield mock

@pytest.fixture
def mock_backend_client():
    with patch("src.mcp.lib.decorators.backend_client") as mock:
        yield mock

@pytest.mark.asyncio
async def test_get_mcp_token_exchanges_and_caches(mock_httpx_client):
    """T010: Verify get_mcp_token exchanges token and caches it."""
    # Setup mocks
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "exchanged_mcp_token"}
    mock_response.raise_for_status.return_value = None
    
    mock_client_instance = AsyncMock()
    mock_client_instance.post.return_value = mock_response
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
    
    user_token = "valid_user_token"
    
    # 1. First call - should trigger exchange
    token1 = await get_mcp_token(user_token)
    assert token1 == "exchanged_mcp_token"
    assert mock_client_instance.post.call_count == 1
    
    # Verify request params
    call_args = mock_client_instance.post.call_args
    assert call_args[0][0].endswith("/v1/token")
    assert call_args[1]["data"]["grant_type"] == "urn:ietf:params:oauth:grant-type:token-exchange"
    assert call_args[1]["data"]["subject_token"] == user_token
    assert call_args[1]["data"]["scope"] == "mcp:use"

    # 2. Second call with same user token - should use cache (no new request)
    token2 = await get_mcp_token(user_token)
    assert token2 == "exchanged_mcp_token"
    assert mock_client_instance.post.call_count == 1  # Still 1

@pytest.mark.asyncio
async def test_mcp_tool_uses_exchanged_token(mock_backend_client):
    """T015: Verify tool wrapper uses exchanged token."""
    # Mock context with user token
    ctx = MagicMock(spec=Context)
    # Configure the mock to have attributes that return what we want
    # We need to simulate ctx.request.headers or ctx.session.metadata
    
    # Simulate extraction logic finding token in request headers
    request_mock = MagicMock()
    request_mock.headers = {"Authorization": "Bearer user_token_123"}
    ctx.request = request_mock
    ctx.session = None # Ensure it falls back to request
    
    # Mock get_mcp_token to avoid real HTTP call
    with patch("src.mcp.lib.decorators.get_mcp_token", new_callable=AsyncMock) as mock_get_token, \
         patch("src.mcp.lib.decorators.authenticate_and_authorize", new_callable=AsyncMock) as mock_auth:
        
        # Setup mock auth success
        mock_principal = MagicMock()
        mock_principal.subject = "EMP001"
        mock_auth.return_value = ("user_token_123", mock_principal, None)
        
        mock_get_token.return_value = "scoped_mcp_token_abc"
        
        # Mock backend response
        # call_action is awaited, so it must return an awaitable or be an AsyncMock
        mock_backend_client.call_action = AsyncMock(return_value={"data": {"name": "Test Employee"}})
        
        # Invoke tool
        result = await hcm.get_employee(ctx, "EMP001")
        
        # Verify get_mcp_token was called with user token
        mock_get_token.assert_awaited_once_with("user_token_123")
        
        # Verify backend was called with EXCHANGED token
        mock_backend_client.call_action.assert_awaited_once()
        call_kwargs = mock_backend_client.call_action.call_args[1]
        assert call_kwargs["token"] == "scoped_mcp_token_abc"