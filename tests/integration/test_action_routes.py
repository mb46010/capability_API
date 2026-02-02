import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.domain.services.policy_engine import PolicyEvaluationResult

@pytest.mark.asyncio
async def test_action_execution_success(mock_policy_engine, machine_token):
    # Mock Policy Allow
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=True)
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {machine_token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "EMP001"}},
            headers=headers
        )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "provenance" in data["meta"]

@pytest.mark.asyncio
async def test_action_execution_forbidden(mock_policy_engine, machine_token):
    # Mock Policy Deny
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=False)
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {machine_token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/delete_employee",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    # Should be 403 Forbidden
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_action_execution_unauthorized():
    # No token provided
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "123"}}
        )
    
    assert response.status_code == 401