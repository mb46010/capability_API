import pytest
import jwt
import json
from unittest.mock import AsyncMock, patch, MagicMock
from src.mcp.tools.discovery import list_available_tools

@pytest.mark.asyncio
async def test_available_tools_discovery(issue_token):
    """Verify that different personas discover only their authorized tools."""
    
    # 1. AI Agent
    agent_token = issue_token(subject="agent-1", principal_type="AI_AGENT")
    mock_ctx = MagicMock()
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {agent_token}"}}
    
    result = await list_available_tools(mock_ctx)
    data = json.loads(result)
    assert "get_employee" in data["available_tools"]
    assert "get_compensation" not in data["available_tools"]
    assert data["role"] == "AI_AGENT"

    # 2. Employee (Human + groups)
    emp_token = issue_token(subject="emp-1", principal_type="HUMAN", groups=["employees"])
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {emp_token}"}}
    
    result = await list_available_tools(mock_ctx)
    data = json.loads(result)
    assert "request_time_off" in data["available_tools"]
    assert "approve_time_off" not in data["available_tools"]

    # 3. Admin
    admin_token = issue_token(subject="admin-1", principal_type="HUMAN", groups=["hr-platform-admins"])
    mock_ctx.session = {"metadata": {"Authorization": f"Bearer {admin_token}"}}
    
    result = await list_available_tools(mock_ctx)
    data = json.loads(result)
    assert "get_compensation" in data["available_tools"]
    assert "approve_time_off" in data["available_tools"]
    assert len(data["available_tools"]) > 10 # Admins see almost everything