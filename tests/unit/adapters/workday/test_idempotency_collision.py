import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig

@pytest.fixture
def simulator():
    config = WorkdaySimulationConfig(
        idempotency_cache_max_size=10,
        idempotency_cache_ttl=60
    )
    with patch("src.adapters.workday.client.FixtureLoader") as MockLoader:
        instance = MockLoader.return_value
        emp_mock = MagicMock()
        emp_mock.manager = None
        instance.employees = {"EMP001": emp_mock}
        instance.departments = {}
        instance.balances = {}
        instance.requests = {}
        instance.compensation = {}
        instance.statements = {}
        return WorkdaySimulator(config)

@pytest.mark.asyncio
async def test_idempotency_collision_different_actions(simulator):
    """
    Test that two different actions with the same idempotency key do NOT collide (Fixed).
    """
    simulator.hcm_service.update_employee = AsyncMock(return_value={"action": "update_employee"})
    simulator.hcm_service.terminate_employee = AsyncMock(return_value={"action": "terminate_employee"})
    
    key = "same-key"
    
    # First call: update_employee
    res1 = await simulator.execute("workday.hcm.update_employee", {"idempotency_key": key, "employee_id": "EMP001"})
    assert res1 == {"action": "update_employee"}
    
    # Second call: terminate_employee with SAME key
    res2 = await simulator.execute("workday.hcm.terminate_employee", {"idempotency_key": key, "employee_id": "EMP001"})
    
    # FIXED: res2 should be {"action": "terminate_employee"}
    assert res2 == {"action": "terminate_employee"}
    assert simulator.hcm_service.terminate_employee.call_count == 1

@pytest.mark.asyncio
async def test_idempotency_collision_different_principals(simulator):
    """
    Test that two different principals with the same idempotency key do NOT collide (Fixed).
    """
    simulator.hcm_service.update_employee = AsyncMock(side_effect=lambda p: {"principal_id": p.get("principal_id")})
    
    key = "same-key"
    
    # Principal A
    res1 = await simulator.execute("workday.hcm.update_employee", {
        "idempotency_key": key, 
        "employee_id": "EMP001",
        "principal_id": "principal-A"
    })
    assert res1 == {"principal_id": "principal-A"}
    
    # Principal B with SAME key
    res2 = await simulator.execute("workday.hcm.update_employee", {
        "idempotency_key": key, 
        "employee_id": "EMP001",
        "principal_id": "principal-B"
    })
    
    # FIXED: res2 should be {"principal_id": "principal-B"}
    assert res2 == {"principal_id": "principal-B"}
    assert simulator.hcm_service.update_employee.call_count == 2
