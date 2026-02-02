import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch, MagicMock
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig

@pytest.fixture
def simulator():
    config = WorkdaySimulationConfig(
        idempotency_cache_max_size=3,
        idempotency_cache_ttl=1 # 1 second for easy testing
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
async def test_idempotency_cache_hit(simulator):
    """Test that subsequent calls with same key return cached result."""
    simulator.hcm_service.update_employee = AsyncMock(return_value={"status": "updated"})
    
    params = {"employee_id": "EMP001", "idempotency_key": "key-1"}
    
    # First call
    result1 = await simulator.execute("workday.hcm.update_employee", params)
    assert result1 == {"status": "updated"}
    assert simulator.hcm_service.update_employee.call_count == 1
    
    # Second call with same key
    result2 = await simulator.execute("workday.hcm.update_employee", params)
    assert result2 == {"status": "updated"}
    # Service should NOT be called again
    assert simulator.hcm_service.update_employee.call_count == 1

@pytest.mark.asyncio
async def test_idempotency_cache_eviction_lru(simulator):
    """Test that oldest entries are evicted when cache reaches max size."""
    simulator.hcm_service.update_employee = AsyncMock(side_effect=lambda p: {"key": p["idempotency_key"]})
    
    # Fill cache up to max_size (3)
    await simulator.execute("workday.hcm.update_employee", {"idempotency_key": "key-1"})
    await simulator.execute("workday.hcm.update_employee", {"idempotency_key": "key-2"})
    await simulator.execute("workday.hcm.update_employee", {"idempotency_key": "key-3"})
    
    assert len(simulator._idempotency_cache) == 3
    assert "key-1" in simulator._idempotency_cache
    
    # Add one more, should evict key-1 (the oldest)
    await simulator.execute("workday.hcm.update_employee", {"idempotency_key": "key-4"})
    
    assert len(simulator._idempotency_cache) == 3
    assert "key-1" not in simulator._idempotency_cache
    assert "key-4" in simulator._idempotency_cache

@pytest.mark.asyncio
async def test_idempotency_cache_ttl(simulator):
    """Test that expired entries are evicted."""
    simulator.hcm_service.update_employee = AsyncMock(return_value={"status": "ok"})
    
    # Set entry with TTL=1
    await simulator.execute("workday.hcm.update_employee", {"idempotency_key": "key-1"})
    assert "key-1" in simulator._idempotency_cache
    
    # Wait for expiration
    await asyncio.sleep(1.1)
    
    # Should not be in cache anymore when trying to get it
    cached = simulator._get_cached("key-1")
    assert cached is None
    assert "key-1" not in simulator._idempotency_cache

@pytest.mark.asyncio
async def test_idempotency_only_on_write_ops(simulator):
    """Test that read operations (no 'update' etc in action name) are not cached."""
    simulator.hcm_service.get_employee = AsyncMock(return_value={"employee_id": "EMP001"})
    
    params = {"employee_id": "EMP001", "idempotency_key": "key-read"}
    
    # First call
    await simulator.execute("workday.hcm.get_employee", params)
    assert len(simulator._idempotency_cache) == 0
    
    # Second call
    await simulator.execute("workday.hcm.get_employee", params)
    assert simulator.hcm_service.get_employee.call_count == 2
