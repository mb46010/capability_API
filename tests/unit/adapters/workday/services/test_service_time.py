import pytest
from unittest.mock import MagicMock
from datetime import date
from src.adapters.workday.services.time import WorkdayTimeService
from src.adapters.workday.domain.time_models import TimeOffBalance
from src.adapters.workday.domain.hcm_models import Employee, EmployeeName, EmployeeJob
from src.adapters.workday.domain.types import EmployeeStatus
from src.adapters.workday.exceptions import InsufficientBalanceError, InvalidDateRangeError

@pytest.fixture
def mock_state():
    state = MagicMock()
    # Setup dummy employee
    state.employees = {
        "EMP001": Employee(
            employee_id="EMP001",
            name=EmployeeName(first="Alice", last="Johnson", display="Alice Johnson"),
            email="alice@example.com",
            job=EmployeeJob(title="Engineer", department="Eng", department_id="D1", location="US"),
            status=EmployeeStatus.ACTIVE,
            start_date="2023-01-01"
        )
    }
    # Setup dummy balances
    state.balances = {
        "EMP001": [
            TimeOffBalance(
                type="PTO", type_name="Paid Time Off",
                available_hours=40, used_hours=0, pending_hours=0,
                accrual_rate_per_period=5, max_carryover=80
            )
        ]
    }
    state.requests = {}
    # Setup config
    state.config = MagicMock()
    state.config.enforce_balance_check = True
    return state

@pytest.fixture
def service(mock_state):
    return WorkdayTimeService(mock_state)

@pytest.mark.asyncio
async def test_get_balance_success(service):
    result = await service.get_balance({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    assert len(result["balances"]) == 1
    assert result["balances"][0]["available_hours"] == 40

@pytest.mark.asyncio
async def test_request_time_off_success(service):
    result = await service.request({
        "employee_id": "EMP001",
        "type": "PTO",
        "start_date": "2026-06-01",
        "end_date": "2026-06-02",
        "hours": 16,
        "notes": "Vacation"
    })
    
    assert result["status"] == "PENDING"
    assert "request_id" in result
    # Check if pending hours updated in state
    assert service.state.balances["EMP001"][0].pending_hours == 16

@pytest.mark.asyncio
async def test_request_insufficient_balance(service):
    with pytest.raises(InsufficientBalanceError):
        await service.request({
            "employee_id": "EMP001",
            "type": "PTO",
            "start_date": "2026-06-01",
            "end_date": "2026-06-10",
            "hours": 80 # > 40 available
        })

@pytest.mark.asyncio
async def test_request_invalid_dates(service):
    with pytest.raises(InvalidDateRangeError):
        await service.request({
            "employee_id": "EMP001",
            "type": "PTO",
            "start_date": "2026-06-05",
            "end_date": "2026-06-01", # End before start
            "hours": 8
        })
