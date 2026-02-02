import pytest
from unittest.mock import AsyncMock, patch
from src.mcp.tools.hcm import get_employee
from src.mcp.adapters.auth import PrincipalContext

@pytest.mark.asyncio
@patch("src.mcp.lib.decorators.backend_client.call_action")
async def test_get_employee_success(mock_call):
    # Mock successful backend response
    mock_call.return_value = {
        "data": {
            "employee_id": "EMP001",
            "name": {"first": "John", "last": "Doe", "display": "John Doe"},
            "job": {"title": "Engineer", "department": "IT", "location": "NYC"},
            "status": "ACTIVE"
        }
    }
    
    # Mock auth context via some mechanism (we'll need to define how tools get context)
    # For now, let's assume we have a helper or the tool takes it.
    # In FastMCP, we might use session context.
    
    # This is a unit test for the logic inside the tool.
    # We'll refine the implementation of the tool to handle context correctly.
    pass

# We'll add more tests as we implement the tools.
