import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from src.domain.services.action_service import ActionService
from src.lib.config_validator import settings

@pytest.mark.asyncio
async def test_direct_api_access_with_mcp_token_rejected():
    """T019: Verify direct API access with mcp:use token is rejected without acting_through context."""
    mock_policy_engine = MagicMock()
    mock_policy_engine.evaluate.return_value.allowed = True
    
    mock_connector = MagicMock()
    
    service = ActionService(policy_engine=mock_policy_engine, connector=mock_connector)
    
    # Mock audit logger to avoid errors if it's called
    service.audit_logger = MagicMock()
    
    # Case 1: Token has mcp:use but NO acting_through context -> REJECT
    token_claims_valid_but_direct = {
        "scope": ["mcp:use"],
        "sub": "user@example.com",
        "cid": settings.MCP_CLIENT_ID, # Valid client ID
        "acting_as": "mcp-server" 
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
            token_claims=token_claims_valid_but_direct,
            acting_through=None # Explicitly missing header context
        )
    assert exc.value.status_code == 403
    assert "MCP-scoped tokens cannot be used for direct API access" in exc.value.detail

@pytest.mark.asyncio
async def test_api_access_with_mcp_token_and_acting_through_allowed():
    """T031: Verify API access with mcp:use token is allowed with acting_through context."""
    mock_policy_engine = MagicMock()
    mock_policy_engine.evaluate.return_value.allowed = True
    mock_policy_engine.evaluate.return_value.policy_name = "test-policy"
    mock_policy_engine.evaluate.return_value.audit_level = "BASIC"
    
    mock_connector = AsyncMock()
    mock_connector.execute.return_value = {"status": "success"}
    
    service = ActionService(policy_engine=mock_policy_engine, connector=mock_connector)
    
    token_claims = {
        "scope": ["mcp:use"],
        "sub": "user@example.com",
        "cid": settings.MCP_CLIENT_ID,
        "acting_as": "mcp-server"
    }
    
    response = await service.execute_action(
        domain="workday.hcm",
        action="get_employee",
        parameters={"employee_id": "123"},
        principal_id="user@example.com",
        principal_groups=["employees"],
        principal_type="HUMAN",
        environment="local",
        token_claims=token_claims,
        acting_through="mcp-server" # Provided via header in real API
    )
    
    assert response.data == {"status": "success"}

@pytest.mark.asyncio
async def test_mcp_token_spoofing_rejected():
    """T032: Verify that MCP-scoped tokens from unauthorized clients are rejected even if they spoof the header."""
    mock_policy_engine = MagicMock()
    mock_policy_engine.evaluate.return_value.allowed = True
    
    mock_connector = AsyncMock()
    
    service = ActionService(policy_engine=mock_policy_engine, connector=mock_connector)
    
    # ❌ This token belongs to 'attacker-client', but has 'mcp:use' scope
    token_claims_attacker = {
        "scope": ["mcp:use"],
        "sub": "user@example.com",
        "cid": "attacker-client" # Unauthorized client
    }
    
    # Should be REJECTED because cid != MCP_CLIENT_ID
    with pytest.raises(HTTPException) as exc:
        await service.execute_action(
            domain="workday.hcm",
            action="get_employee",
            parameters={"employee_id": "123"},
            principal_id="user@example.com",
            principal_groups=["employees"],
            principal_type="HUMAN",
            environment="local",
            token_claims=token_claims_attacker,
            acting_through="mcp-server" # Spoofed header
        )
    
    assert exc.value.status_code == 403
    assert "MCP-scoped tokens must originate from the authorized MCP client" in exc.value.detail
