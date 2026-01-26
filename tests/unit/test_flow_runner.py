import pytest
from src.domain.services.flow_runner import FlowRunner
from src.domain.ports.flow_runner import FlowRunnerPort
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
def flow_runner():
    adapter = MockFlowAdapter()
    return FlowRunner(adapter)

@pytest.mark.asyncio
async def test_start_flow_success(flow_runner):
    # Test starting a flow
    # Assuming Policy Check is done in Service/Route layer or we mock it here if we inject PolicyEngine
    
    flow_id = await flow_runner.start_flow("hr", "onboarding", {"employee_id": "123"})
    assert flow_id == "test-flow-123"

@pytest.mark.asyncio
async def test_get_flow_status_success(flow_runner):
    # Setup state
    await flow_runner.start_flow("hr", "onboarding", {"employee_id": "123"})
    
    status = await flow_runner.get_status("test-flow-123")
    assert status.flow_id == "test-flow-123"
    assert status.status == "RUNNING"
