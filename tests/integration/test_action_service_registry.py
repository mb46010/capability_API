import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from src.domain.services.action_service import ActionService
from src.domain.services.capability_registry import CapabilityRegistryService
from src.domain.entities.capability import CapabilityEntry, CapabilityType, SensitivityLevel

@pytest.fixture
def mock_registry():
    registry = MagicMock(spec=CapabilityRegistryService)
    registry.exists.side_effect = lambda x: x in ["workday.hcm.get_employee", "workday.payroll.get_pay_statement"]
    
    # Mock get() for deprecation check
    def mock_get(cap_id):
        if cap_id == "workday.payroll.get_pay_statement":
            return CapabilityEntry(
                id=cap_id, name="n", domain="d", type=CapabilityType.ACTION, 
                sensitivity=SensitivityLevel.LOW, deprecated=True
            )
        return CapabilityEntry(
            id=cap_id, name="n", domain="d", type=CapabilityType.ACTION, 
            sensitivity=SensitivityLevel.LOW, deprecated=False
        )
    registry.get.side_effect = mock_get
    registry._find_similar.return_value = ["workday.hcm.get_employee"]
    return registry

@pytest.fixture
def action_service(mock_registry):
    policy_engine = MagicMock()
    connector = MagicMock()
    # Use AsyncMock for the execute method since it's awaited
    connector.execute = AsyncMock()
    service = ActionService(policy_engine, connector, registry=mock_registry)
    return service

@pytest.mark.asyncio
async def test_validate_unknown_capability(action_service):
    with pytest.raises(HTTPException) as exc:
        action_service._validate_capability("workday.hcm", "get_employe") # Typo
    
    assert exc.value.status_code == 400
    assert "Unknown capability" in exc.value.detail
    assert "workday.hcm.get_employee" in exc.value.detail

@pytest.mark.asyncio
async def test_validate_valid_capability(action_service):
    # Should not raise
    action_service._validate_capability("workday.hcm", "get_employee")

@pytest.mark.asyncio
@patch("src.domain.services.action_service.logger")
async def test_deprecated_capability_warning(mock_logger, action_service):
    # Setup mock for successful execution path
    action_service.policy_engine.evaluate.return_value = MagicMock(allowed=True, policy_name="test", audit_level="BASIC")
    action_service.connector.execute.return_value = {"data": "ok"}
    
    await action_service.execute_action(
        domain="workday.payroll",
        action="get_pay_statement",
        parameters={},
        principal_id="user1",
        principal_groups=[],
        principal_type="HUMAN",
        environment="local"
    )
    
    # Check if warning was logged
    mock_logger.warning.assert_called()
    args, _ = mock_logger.warning.call_args
    assert "deprecated" in args[0]