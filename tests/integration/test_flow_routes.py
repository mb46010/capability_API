import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider, get_policy_engine
from src.domain.services.policy_engine import PolicyEngine, PolicyEvaluationResult

@pytest.fixture
def mock_policy_engine(mocker):
    return mocker.Mock(spec=PolicyEngine)

@pytest.fixture(autouse=True)
def override_dependencies(mock_policy_engine):
    app.dependency_overrides[get_policy_engine] = lambda: mock_policy_engine
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_start_flow_success(mock_policy_engine):
    # Mock Policy Allow
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=True)
    
    token = provider.issue_token(subject="admin-user", groups=["admins"], principal_type="HUMAN")
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {token}"
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
async def test_start_flow_forbidden(mock_policy_engine):
    # Mock Policy Deny
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=False)
    
    token = provider.issue_token(subject="test-worker-1", principal_type="MACHINE")
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/flows/hr/onboarding",
            json={"parameters": {"employee_id": "123"}},
            headers=headers
        )
    
    # Should be 403 Forbidden
    assert response.status_code == 403
