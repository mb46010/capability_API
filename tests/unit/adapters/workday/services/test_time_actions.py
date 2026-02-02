import pytest
from src.adapters.workday.services.time import WorkdayTimeService
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def service(simulator):
    """Fresh WorkdayTimeService instance using shared simulator."""
    return WorkdayTimeService(simulator)

@pytest.mark.asyncio
async def test_get_balance_success(service):
    result = await service.get_balance({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    # The real fixture has 1 balance type: PTO
    assert len(result["balances"]) >= 1
    assert any(b["type"] == "PTO" for b in result["balances"])

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

