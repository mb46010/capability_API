import pytest
from unittest.mock import MagicMock
from src.adapters.workday.services.time import WorkdayTimeService
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def mock_simulator():
    sim = MagicMock()
    class MockAttr:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        def model_dump(self):
            return self.__dict__

    # Mock balances
    sim.balances = {
        "EMP001": [
            MockAttr(type="PTO", available_hours=100, used_hours=20, pending_hours=0),
            MockAttr(type="SICK", available_hours=40, used_hours=5, pending_hours=0)
        ]
    }
    sim.requests = {}
    sim.employees = {
        "EMP001": MockAttr(employee_id="EMP001", manager=MockAttr(employee_id="EMP042", display_name="Bob")),
        "EMP042": MockAttr(employee_id="EMP042", manager=None)
    }
    return sim

@pytest.fixture
def service(mock_simulator):
    return WorkdayTimeService(mock_simulator)

@pytest.mark.asyncio
async def test_get_balance_success(service):
    result = await service.get_balance({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    assert len(result["balances"]) == 2
    assert result["balances"][0]["type"] == "PTO"

@pytest.mark.asyncio
async def test_get_balance_own_data_enforcement(service):
    params = {"employee_id": "EMP001", "principal_id": "EMP002", "principal_type": "HUMAN"}
    with pytest.raises(WorkdayError) as exc:
        await service.get_balance(params)
    assert exc.value.error_code == "UNAUTHORIZED"

@pytest.mark.asyncio
async def test_request_time_off_success(service):
    params = {
        "employee_id": "EMP001",
        "type": "PTO",
        "start_date": "2026-03-01",
        "end_date": "2026-03-05",
        "hours": 40,
        "principal_id": "EMP001", 
        "principal_type": "HUMAN"
    }
    result = await service.request(params)
    assert result["status"] == "PENDING"
    assert result["request_id"].startswith("TOR-")

@pytest.mark.asyncio
async def test_approve_time_off_success(service):
    class SimpleReq:
        def __init__(self, **kwargs): self.__dict__.update(kwargs)
    
    req_id = "TOR-APPROVE-001"
    service.simulator.requests[req_id] = SimpleReq(
        request_id=req_id,
        employee_id="EMP001",
        status="PENDING",
        hours=40,
        type="PTO"
    )
    
    params = {
        "request_id": req_id,
        "principal_id": "EMP042", # Manager
        "principal_type": "HUMAN",
        "mfa_verified": True
    }
    result = await service.approve(params)
    assert result["status"] == "APPROVED"

