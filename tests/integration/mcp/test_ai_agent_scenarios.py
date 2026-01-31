import pytest
import jwt
from unittest.mock import AsyncMock, patch, MagicMock
# from src.mcp.server import mcp
from src.mcp.adapters.auth import PrincipalContext

@pytest.mark.asyncio
async def test_ai_agent_get_employee_filtered():
    """
    Integration-style test for AI Agent lookup.
    Mocks the backend response and verifies the MCP tool passes it through.
    """
    # 1. Create a mock token for AI Agent
    token_payload = {
        "sub": "agent-001",
        "principal_type": "AI_AGENT",
        "groups": ["agents"]
    }
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    # 2. Mock the backend response (filtered as if by the Capability API)
    mock_backend_response = {
        "data": {
            "employee_id": "EMP001",
            "name": {"display": "John Doe"},
            "job": {"title": "Engineer", "department": "IT"},
            "status": "ACTIVE"
            # Sensitive fields like 'personal_email' are already removed by backend
        },
        "meta": {"provenance": {"actor": "agent-001"}}
    }
    
    # 3. Execute the tool via mcp instance (mocking the context/session)
    # We'll use a patch for the backend client
    with patch("src.mcp.tools.hcm.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_backend_response
        
        # Mock Context
        mock_ctx = MagicMock()
        mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
        
        # Import the tool function directly or call via mcp
        from src.mcp.tools.hcm import get_employee
        result = await get_employee(mock_ctx, "EMP001")
        
        # 4. Verify
        assert "EMP001" in result
        assert "John Doe" in result
        assert "personal_email" not in result # Verifying the backend's filtering is preserved
        mock_call.assert_called_once()

@pytest.mark.asyncio
async def test_ai_agent_update_contact_info():
    """Verify AI Agent can call update_contact_info (No MFA required in MCP)."""
    token_payload = {"sub": "agent-001", "principal_type": "AI_AGENT"}
    token = jwt.encode(token_payload, "secret", algorithm="HS256")
    
    mock_backend_response = {"data": {"status": "APPLIED", "transaction_id": "TXN-123"}}
    
    with patch("src.mcp.tools.hcm.backend_client.call_action", new_callable=AsyncMock) as mock_call:
        mock_call.return_value = mock_backend_response
        mock_ctx = MagicMock()
        mock_ctx.session = {"metadata": {"Authorization": f"Bearer {token}"}}
        
        from src.mcp.tools.hcm import update_contact_info
        result = await update_contact_info(mock_ctx, "EMP001", {"personal_email": "new@test.com"})
        
        assert "APPLIED" in result
        mock_call.assert_called_once()
