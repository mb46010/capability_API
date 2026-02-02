import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider, get_flow_runner_adapter
from src.domain.ports.flow_runner import FlowRunnerPort

class MockFlowRunner(FlowRunnerPort):
    async def start_flow(self, domain, flow, params, principal_id):
        return "flow-123"
    async def get_flow_status(self, flow_id):
        if flow_id == "existing-flow":
            return {
                "flow_id": "existing-flow",
                "status": "RUNNING",
                "principal_id": "owner-user"
            }
        return None

@pytest.fixture
def mock_flow_runner():
    return MockFlowRunner()

@pytest.fixture(autouse=True)
def override_flow_runner(mock_flow_runner):
    app.dependency_overrides[get_flow_runner_adapter] = lambda: mock_flow_runner
    yield
    app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_flow_status_enumeration_vulnerability():
    # Token for a non-admin user who doesn't own any flows
    token = provider.issue_token(subject="attacker-user", groups=["workers"], principal_type="HUMAN")
    
    transport = ASGITransport(app=app)
    headers = {
        "Authorization": f"Bearer {token}"
    }
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # 1. Request non-existent flow
        response_nonexistent = await ac.get("/flows/non-existent-flow", headers=headers)
        
        # 2. Request existing flow owned by someone else
        response_unauthorized = await ac.get("/flows/existing-flow", headers=headers)
    
    # FIXED STATE:
    # Both should return 403 Forbidden
    
    print(f"Non-existent: {response_nonexistent.status_code} {response_nonexistent.json()}")
    print(f"Unauthorized: {response_unauthorized.status_code} {response_unauthorized.json()}")
    
    assert response_nonexistent.status_code == 403
    assert response_unauthorized.status_code == 403
    assert response_nonexistent.json()["message"] == "Flow access denied"
    assert response_unauthorized.json()["message"] == "Flow access denied"

@pytest.mark.asyncio
async def test_flow_status_legitimate_access():
    transport = ASGITransport(app=app)
    
    # 1. Owner access
    owner_token = provider.issue_token(subject="owner-user", groups=["workers"], principal_type="HUMAN")
    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_owner = await ac.get("/flows/existing-flow", headers=headers_owner)
    
    assert response_owner.status_code == 200
    assert response_owner.json()["flow_id"] == "existing-flow"

    # 2. Admin access
    admin_token = provider.issue_token(subject="admin-user", groups=["hr-platform-admins"], principal_type="HUMAN")
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response_admin = await ac.get("/flows/existing-flow", headers=headers_admin)
    
    assert response_admin.status_code == 200
    assert response_admin.json()["flow_id"] == "existing-flow"

