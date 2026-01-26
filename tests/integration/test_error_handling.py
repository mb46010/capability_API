import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider

@pytest.mark.asyncio
async def test_error_response_structure():
    # Trigger a 401 (Unauthorized)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "123"}}
            # No Auth headers
        )
    
    assert response.status_code == 401
    data = response.json()
    
    # Verify ErrorResponse structure
    assert "error_code" in data
    assert "message" in data
    assert data["error_code"] == "401"
    assert data["message"] == "Missing authorization header"

@pytest.mark.asyncio
async def test_error_response_forbidden_structure():
    # Issue a token for a principal that exists but doesn't have this capability
    token = provider.issue_token(subject="test-worker-1", principal_type="MACHINE")
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/delete_employee",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    assert response.status_code == 403
    data = response.json()
    
    assert "error_code" in data
    assert "message" in data
    assert data["error_code"] == "403"
    assert "Access denied" in data["message"]
