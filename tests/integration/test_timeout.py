import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.lib.config_validator import settings

@pytest.mark.asyncio
async def test_request_timeout_middleware(monkeypatch):
    # Set a very low timeout for testing
    monkeypatch.setattr(settings, "REQUEST_TIMEOUT_SECONDS", 0.1)
    
    # Define a slow route dynamically for testing
    @app.get("/test-slow-route")
    async def slow_route():
        await asyncio.sleep(0.5)
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/test-slow-route")
    
    assert response.status_code == 504
    data = response.json()
    assert data["error_code"] == "GATEWAY_TIMEOUT"
    assert "Request timed out" in data["message"]
    assert data["details"]["timeout_seconds"] == 0.1
    
    # Verify X-Request-ID is still present (added by the outer middleware)
    assert "X-Request-ID" in response.headers

@pytest.mark.asyncio
async def test_request_within_timeout(monkeypatch):
    # Set a reasonable timeout
    monkeypatch.setattr(settings, "REQUEST_TIMEOUT_SECONDS", 1.0)
    
    @app.get("/test-fast-route")
    async def fast_route():
        return {"status": "ok"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/test-fast-route")
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers
