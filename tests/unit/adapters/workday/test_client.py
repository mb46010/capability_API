import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig
from src.adapters.workday.exceptions import ConnectorTimeoutError, ConnectorUnavailableError, WorkdayError

@pytest_asyncio.fixture
async def simulator():
    config = WorkdaySimulationConfig()
    # Mocking the loader to avoid disk I/O during unit tests
    with patch("src.adapters.workday.client.FixtureLoader") as MockLoader:
        instance = MockLoader.return_value
        
        # Create a dummy employee without a manager to pass validation
        emp_mock = MagicMock()
        emp_mock.manager = None
        instance.employees = {"EMP001": emp_mock}
        
        instance.departments = {}
        instance.balances = {}
        instance.requests = {}
        instance.compensation = {}
        instance.statements = {}
        yield WorkdaySimulator(config)

@pytest.mark.asyncio
async def test_execute_dispatch_success(simulator):
    """Test that execute correctly dispatches to a service method."""
    # Mock the hcm_service.get_employee method
    simulator.hcm_service.get_employee = AsyncMock(return_value={"employee_id": "EMP001"})
    
    result = await simulator.execute("workday.hcm.get_employee", {"employee_id": "EMP001"})
    
    assert result == {"employee_id": "EMP001"}
    simulator.hcm_service.get_employee.assert_called_once_with({"employee_id": "EMP001"})

@pytest.mark.asyncio
async def test_execute_not_implemented(simulator):
    """Test that execute raises WorkdayError for unknown actions."""
    with pytest.raises(WorkdayError) as excinfo:
        await simulator.execute("workday.unknown.action", {})
    
    assert excinfo.value.error_code == "NOT_IMPLEMENTED"

@pytest.mark.asyncio
async def test_failure_injection_unavailable():
    """Test failure injection: 100% chance of unavailability."""
    config = WorkdaySimulationConfig(failure_rate=1.0) # Always fail
    with patch("src.adapters.workday.client.FixtureLoader") as MockLoader:
        instance = MockLoader.return_value
        emp_mock = MagicMock()
        emp_mock.manager = None
        instance.employees = {"EMP001": emp_mock}
        
        simulator = WorkdaySimulator(config)
        
        with pytest.raises(ConnectorUnavailableError):
            await simulator.execute("workday.hcm.get_employee", {})

@pytest.mark.asyncio
async def test_failure_injection_timeout():
    """Test failure injection: 100% chance of timeout."""
    config = WorkdaySimulationConfig(timeout_rate=1.0) # Always timeout
    with patch("src.adapters.workday.client.FixtureLoader") as MockLoader:
        instance = MockLoader.return_value
        emp_mock = MagicMock()
        emp_mock.manager = None
        instance.employees = {"EMP001": emp_mock}
        
        simulator = WorkdaySimulator(config)
        
        with pytest.raises(ConnectorTimeoutError):
            await simulator.execute("workday.hcm.get_employee", {})

@pytest.mark.asyncio
async def test_latency_simulation():
    """Test that latency simulation is called."""
    # Set high base latency and low variance to ensure delay_ms > 0
    config = WorkdaySimulationConfig(base_latency_ms=100, latency_variance_ms=0)
    with patch("src.adapters.workday.client.FixtureLoader") as MockLoader:
        instance = MockLoader.return_value
        emp_mock = MagicMock()
        emp_mock.manager = None
        instance.employees = {"EMP001": emp_mock}
        
        simulator = WorkdaySimulator(config)
        
        # Mock the internal _simulate_latency method if we want to check if it's called,
        # OR just mock asyncio.sleep to ensure it waits.
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            # We need a valid handler so execute doesn't fail before latency
            simulator.hcm_service.get_employee = AsyncMock(return_value={})
            
            await simulator.execute("workday.hcm.get_employee", {})
            
            assert mock_sleep.called
