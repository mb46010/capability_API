import pytest
from src.adapters.workday.services.payroll import WorkdayPayrollService
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def service(simulator):
    """Fresh WorkdayPayrollService instance using shared simulator."""
    return WorkdayPayrollService(simulator)

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
    # Real data has 185000
    assert result["compensation"]["base_salary"]["amount"] == 185000

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
