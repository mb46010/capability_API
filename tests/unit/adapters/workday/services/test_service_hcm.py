import pytest
from unittest.mock import MagicMock
from src.adapters.workday.services.hcm import WorkdayHCMService
from src.adapters.workday.domain.hcm_models import Employee, EmployeeName, EmployeeJob
from src.adapters.workday.domain.types import EmployeeStatus
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def mock_state():
    state = MagicMock()
    # Setup dummy data
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
    return state

@pytest.fixture
def service(mock_state):
    return WorkdayHCMService(mock_state)

@pytest.mark.asyncio
async def test_get_employee_success(service):
    result = await service.get_employee({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    assert result["name"]["display"] == "Alice Johnson"

@pytest.mark.asyncio
async def test_get_employee_not_found(service):
    with pytest.raises(WorkdayError) as excinfo:
        await service.get_employee({"employee_id": "NON_EXISTENT"})
    assert str(excinfo.value) == "Access denied"

@pytest.mark.asyncio
async def test_list_direct_reports_empty(service):
    # EMP001 has no reports
    result = await service.list_direct_reports({"manager_id": "EMP001"})
    assert result["count"] == 0
    assert result["direct_reports"] == []

@pytest.mark.asyncio
async def test_update_employee_success(service):
    updates = {"job": {"title": "Senior Engineer"}}
    result = await service.update_employee({"employee_id": "EMP001", "updates": updates})
    
    assert result["employee_id"] == "EMP001"
    assert result["status"] == "PENDING_APPROVAL"
    assert len(result["changes"]) == 1
    assert result["changes"][0]["field"] == "job"
