import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from src.domain.services.action_service import ActionService

@pytest.mark.asyncio
async def test_direct_api_access_with_mcp_token_rejected():
    """T019: Verify direct API access with mcp:use token is rejected without acting_as."""
    mock_policy_engine = MagicMock()
    mock_policy_engine.evaluate.return_value.allowed = True
    
    mock_connector = MagicMock()
    
    service = ActionService(policy_engine=mock_policy_engine, connector=mock_connector)
    
    # Mock audit logger to avoid errors if it's called
    service.audit_logger = MagicMock()
    
    # Case 1: Token has mcp:use but NO acting_as -> REJECT
    token_claims_invalid = {
        "scope": ["mcp:use"],
        "sub": "user@example.com"
        # acting_as is missing
    }
    
    with pytest.raises(HTTPException) as exc:
        await service.execute_action(
            domain="workday.hcm",
            action="get_employee",
            parameters={"employee_id": "123"},
            principal_id="user@example.com",
            principal_groups=["employees"],
            principal_type="HUMAN",
            environment="local",
            token_claims=token_claims_invalid
        )
    assert exc.value.status_code == 403
    assert "MCP-scoped tokens cannot be used for direct API access" in exc.value.detail
