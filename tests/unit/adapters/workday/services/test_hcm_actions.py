import pytest
from unittest.mock import AsyncMock, MagicMock
from src.adapters.workday.services.hcm import WorkdayHCMService
from src.adapters.workday.exceptions import WorkdayError

@pytest.fixture
def mock_simulator():
    sim = MagicMock()
    # Use real objects or better mocks for data
    class MockAttr:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
        def model_dump(self):
            return self.__dict__

    sim.employees = {
        "EMP001": MockAttr(
            employee_id="EMP001",
            name={"first": "Alice", "last": "Johnson", "display": "Alice Johnson"},
            email="alice@example.com",
            job={"title": "Engineer", "department": "Engineering", "location": "San Francisco"},
            manager=MockAttr(employee_id="EMP042", display_name="Bob Manager"),
            status="ACTIVE",
            personal_email="alice.old@gmail.com"
        ),
        "EMP042": MockAttr(
            employee_id="EMP042",
            name={"display": "Bob Manager"},
            job={"title": "Manager"},
            manager=None
        )
    }
    return sim

@pytest.fixture
def service(mock_simulator):
    return WorkdayHCMService(mock_simulator)

@pytest.mark.asyncio
async def test_get_employee_success(service):
    result = await service.get_employee({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    assert result["name"]["display"] == "Alice Johnson"

@pytest.mark.asyncio
async def test_get_employee_not_found(service):
    with pytest.raises(WorkdayError) as exc:
        await service.get_employee({"employee_id": "INVALID"})
    assert exc.value.error_code == "UNAUTHORIZED"
    assert str(exc.value) == "Access denied"

@pytest.mark.asyncio
async def test_get_manager_chain(service):
    result = await service.get_manager_chain({"employee_id": "EMP001"})
    assert result["employee_id"] == "EMP001"
    assert len(result["chain"]) >= 1
    assert result["chain"][0]["employee_id"] == "EMP042"

@pytest.mark.asyncio
async def test_list_direct_reports(service):
    result = await service.list_direct_reports({"manager_id": "EMP042", "principal_id": "EMP042", "principal_type": "HUMAN"})
    assert result["manager_id"] == "EMP042"
    ids = [r["employee_id"] for r in result["direct_reports"]]
    assert "EMP001" in ids

@pytest.mark.asyncio
async def test_update_contact_info_success(service):
    params = {
        "employee_id": "EMP001",
        "updates": {
            "personal_email": "alice.new@gmail.com",
            "phone": {"mobile": "+1-555-9999"}
        },
        "principal_id": "EMP001",
        "principal_type": "HUMAN"
    }
    result = await service.update_contact_info(params)
    assert result["status"] == "APPLIED"
    assert any(c["field"] == "personal_email" for c in result["changes"])
