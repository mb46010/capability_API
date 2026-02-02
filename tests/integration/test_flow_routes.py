import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.domain.services.policy_engine import PolicyEvaluationResult

@pytest.mark.asyncio
async def test_start_flow_success(mock_policy_engine, admin_token):
    # Mock Policy Allow
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=True)
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {admin_token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/flows/hr/onboarding",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "RUNNING"
    assert "flow_id" in data

@pytest.mark.asyncio
async def test_start_flow_forbidden(mock_policy_engine, machine_token):
    # Mock Policy Deny
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=False)
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {machine_token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/flows/hr/onboarding",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    # Should be 403 Forbidden
    assert response.status_code == 403
