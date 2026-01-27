import pytest
from datetime import date
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.exceptions import InsufficientBalanceError

@pytest.mark.asyncio
async def test_time_get_balance():
    simulator = WorkdaySimulator()
    result = await simulator.execute("workday.time.get_balance", {"employee_id": "EMP001"})
    
    assert result["employee_id"] == "EMP001"
    assert len(result["balances"]) >= 1
    assert any(b["type"] == "PTO" for b in result["balances"])

@pytest.mark.asyncio
async def test_time_request_lifecycle():
    simulator = WorkdaySimulator()
    
    # 1. Request
    req_params = {
        "employee_id": "EMP001",
        "type": "PTO",
        "start_date": date(2026, 5, 1),
        "end_date": date(2026, 5, 2),
        "hours": 16
    }
    req_result = await simulator.execute("workday.time.request", req_params)
    request_id = req_result["request_id"]
    assert req_result["status"] == "PENDING"
    
    # 2. Approve
    app_result = await simulator.execute("workday.time.approve", {
        "request_id": request_id,
        "approver_id": "EMP042"
    })
    assert app_result["status"] == "APPROVED"
    
    # 3. Verify balance reduction
    bal_result = await simulator.execute("workday.time.get_balance", {"employee_id": "EMP001"})
    pto_bal = next(b for b in bal_result["balances"] if b["type"] == "PTO")
    # Original was 120. Request 16. Should be 104.
    assert pto_bal["available_hours"] == 104

@pytest.mark.asyncio
async def test_time_insufficient_balance():
    simulator = WorkdaySimulator()
    req_params = {
        "employee_id": "EMP001",
        "type": "PTO",
        "start_date": date(2026, 5, 1),
        "end_date": date(2026, 5, 2),
        "hours": 1000 # Way too much
    }
    with pytest.raises(InsufficientBalanceError):
        await simulator.execute("workday.time.request", req_params)
