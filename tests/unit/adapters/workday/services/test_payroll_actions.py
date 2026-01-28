import pytest
from unittest.mock import MagicMock
from src.adapters.workday.services.payroll import WorkdayPayrollService
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def mock_simulator():
    sim = MagicMock()
    sim.compensation = {
        "EMP001": MagicMock(
            base_salary=MagicMock(amount=100000, currency="USD", frequency="ANNUAL"),
            bonus_target=MagicMock(percentage=10, amount=10000),
            total_compensation=110000,
            pay_grade="L4",
            effective_date="2025-01-01"
        )
    }
    return sim

@pytest.fixture
def service(mock_simulator):
    return WorkdayPayrollService(mock_simulator)

@pytest.mark.asyncio
async def test_get_compensation_success(service):
    # MFA verified
    params = {
        "employee_id": "EMP001",
        "principal_id": "EMP001",
        "principal_type": "HUMAN",
        "mfa_verified": True
    }
    result = await service.get_compensation(params)
    assert result["employee_id"] == "EMP001"
    assert result["compensation"]["base_salary"]["amount"] == 100000

@pytest.mark.asyncio
async def test_get_compensation_no_mfa(service):
    params = {
        "employee_id": "EMP001",
        "principal_id": "EMP001",
        "principal_type": "HUMAN",
        "mfa_verified": False
    }
    with pytest.raises(WorkdayError) as exc:
        await service.get_compensation(params)
    assert exc.value.error_code == "MFA_REQUIRED"

@pytest.mark.asyncio
async def test_get_compensation_unauthorized(service):
    params = {
        "employee_id": "EMP001",
        "principal_id": "EMP002", # Other user
        "principal_type": "HUMAN",
        "mfa_verified": True
    }
    with pytest.raises(WorkdayError) as exc:
        await service.get_compensation(params)
    assert exc.value.error_code == "UNAUTHORIZED"
