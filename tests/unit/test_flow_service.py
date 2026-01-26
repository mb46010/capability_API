import pytest
from fastapi import HTTPException
from src.domain.services.flow_service import FlowService
from src.domain.ports.flow_runner import FlowRunnerPort
from src.domain.services.policy_engine import PolicyEngine, PolicyEvaluationResult
from src.domain.entities.flow import FlowStatusResponse, FlowStartRequest

# Mock FlowRunnerAdapter
class MockFlowAdapter(FlowRunnerPort):
    def __init__(self):
        self.flows = {}

    async def start_flow(self, domain: str, flow: str, params: dict) -> str:
        flow_id = "test-flow-123"
        self.flows[flow_id] = {
            "flow_id": flow_id,
            "status": "RUNNING",
            "domain": domain,
            "flow": flow,
            "params": params
        }
        return flow_id

    async def get_flow_status(self, flow_id: str) -> dict:
        if flow_id in self.flows:
            return self.flows[flow_id]
        return None

@pytest.fixture
def mock_policy_engine(mocker):
    return mocker.Mock(spec=PolicyEngine)

@pytest.fixture
def flow_service(mock_policy_engine):
    adapter = MockFlowAdapter()
    return FlowService(mock_policy_engine, adapter)

@pytest.mark.asyncio
async def test_start_flow_success(flow_service, mock_policy_engine):
    # Setup policy to allow
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=True)
    
    flow_id = await flow_service.start_flow(
        domain="hr",
        flow="onboarding",
        params={"employee_id": "123"},
        principal_id="user1",
        principal_groups=[],
        principal_type="HUMAN",
        environment="local"
    )
    assert flow_id == "test-flow-123"
    
    # Verify policy check was called
    mock_policy_engine.evaluate.assert_called_once()
    args, kwargs = mock_policy_engine.evaluate.call_args
    assert kwargs["capability"] == "hr.onboarding"

@pytest.mark.asyncio
async def test_start_flow_denied(flow_service, mock_policy_engine):
    # Setup policy to deny
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=False)
    
    with pytest.raises(HTTPException) as excinfo:
        await flow_service.start_flow(
            domain="hr",
            flow="shutdown",
            params={},
            principal_id="user1",
            principal_groups=[],
            principal_type="HUMAN",
            environment="local"
        )
    
    assert excinfo.value.status_code == 403

@pytest.mark.asyncio
async def test_get_flow_status_success(flow_service, mock_policy_engine):
    # Start flow first (mock allow)
    mock_policy_engine.evaluate.return_value = PolicyEvaluationResult(allowed=True)
    await flow_service.start_flow("hr", "onboarding", {}, "user", [], "HUMAN", "local")
    
    status = await flow_service.get_status("test-flow-123")
    assert status.flow_id == "test-flow-123"
    assert status.status == "RUNNING"