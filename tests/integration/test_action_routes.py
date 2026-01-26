import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.domain.services.policy_engine import PolicyEngine, PolicyEvaluationResult

# Mock the PolicyEngine dependency
@pytest.fixture
def mock_policy_engine(mocker):
    engine = mocker.Mock(spec=PolicyEngine)
    return engine

@pytest.fixture
def override_dependencies(mock_policy_engine):
    # We will need to implement dependency injection override in main.py or dependencies.py
    # For now, let's assume we can override via app.dependency_overrides
    # But since we haven't implemented the endpoints yet, this test serves as TDD spec.
    return

@pytest.mark.asyncio
async def test_action_execution_success(mocker):
    # Simulate a successful action execution
    # This test expects the endpoint to exist and return 200
    
    transport = ASGITransport(app=app)
    headers = {
        "X-Principal-ID": "test-worker-1",
        "X-Principal-Type": "MACHINE"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    # It should return 200 now that we implemented the route
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert "provenance" in data["meta"]

@pytest.mark.asyncio
async def test_action_execution_forbidden():
    # Simulate denied access
    # We rely on the policy loaded in the app (default mock policy) which might deny this.
    # The default mock policy (config/policy.yaml) doesn't have "delete_employee".
    
    transport = ASGITransport(app=app)
    headers = {
        "X-Principal-ID": "test-worker-1",
        "X-Principal-Type": "MACHINE"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/delete_employee",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    # Should be 403 Forbidden
    assert response.status_code == 403