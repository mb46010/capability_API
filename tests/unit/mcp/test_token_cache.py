import pytest
import time
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from cachetools import TTLCache
import src.mcp.adapters.auth as auth_adapter
from src.mcp.adapters.auth import get_mcp_token

@pytest.fixture(autouse=True)
def clear_cache():
    auth_adapter._mcp_token_cache.clear()

@pytest.mark.asyncio
async def test_mcp_token_cache_bounded():
    """
    Verify that the cache is bounded.
    """
    # Monkeypatch the cache with a small maxsize for testing
    test_cache = TTLCache(maxsize=10, ttl=300)
    with patch("src.mcp.adapters.auth._mcp_token_cache", test_cache):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "mcp_token"}
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client_instance

            # Add 20 unique tokens
            for i in range(20):
                await get_mcp_token(f"user_token_{i}")
            
            # Cache size should be 10, not 20
            assert len(test_cache) == 10
            # Latest tokens should be there
            assert "user_token_19" in test_cache
            # Oldest should be gone
            assert "user_token_0" not in test_cache

@pytest.mark.asyncio
async def test_mcp_token_cache_expiration():
    """
    Verify that entries expire.
    """
    # Monkeypatch the cache with a very short TTL
    test_cache = TTLCache(maxsize=10, ttl=0.1)
    with patch("src.mcp.adapters.auth._mcp_token_cache", test_cache):
        with patch("httpx.AsyncClient") as mock_httpx:
            mock_response = MagicMock()
            mock_response.json.return_value = {"access_token": "mcp_token"}
            mock_response.raise_for_status.return_value = None
            
            mock_client_instance = AsyncMock()
            mock_client_instance.post.return_value = mock_response
            mock_httpx.return_value.__aenter__.return_value = mock_client_instance

            await get_mcp_token("user_token_1")
            assert "user_token_1" in test_cache
            
            # Wait for expiration
            await asyncio.sleep(0.2)
            
            # TTLCache doesn't necessarily remove expired items until access or periodic cleanup
            # but it shouldn't return them.
            assert "user_token_1" not in test_cache