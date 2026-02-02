import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider

@pytest.mark.asyncio
async def test_employee_response_matches_openapi():
    """Verify employee response structure matches OpenAPI spec"""
    # Issue a token for an admin
    token = provider.issue_token(
        subject="admin@local.test",
        principal_type="HUMAN",
        groups=["hr-platform-admins"]
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "EMP001"}},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure matches OpenAPI wrapper (data + meta)
    assert "data" in data
    assert "meta" in data
    
    employee = data["data"]
    assert isinstance(employee["start_date"], str)  # Should be string (ISO format)
    assert "employee_id" in employee
    assert "name" in employee
    assert "display" in employee["name"]
    
    # Check manager reference structure
    if employee.get("manager"):
        assert isinstance(employee["manager"], dict)
        assert "employee_id" in employee["manager"]
        assert "display_name" in employee["manager"]

@pytest.mark.asyncio
async def test_error_response_matches_openapi():
    """Verify error responses match OpenAPI spec (semantic codes)"""
    # Unauthorized user (no groups) trying to access sensitive data
    token = provider.issue_token(
        subject="unauthorized@local.test",
        principal_type="HUMAN",
        groups=[]
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_compensation",
            json={"parameters": {"employee_id": "EMP001"}},
            headers={"Authorization": f"Bearer {token}"}
        )
    
    assert response.status_code == 403
    error = response.json()
    
    # Check error structure
    assert "error_code" in error
    assert "message" in error
    assert error["error_code"] == "FORBIDDEN"  # Standardized code
    assert isinstance(error["message"], str)

@pytest.mark.asyncio
async def test_workday_not_found_error():
    """Verify Workday-specific 403 errors for non-existent resources (enumeration protection)"""
    token = provider.issue_token(
        subject="admin@local.test",
        principal_type="HUMAN",
        groups=["hr-platform-admins"]
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/actions/workday/get_employee",
            json={"parameters": {"employee_id": "EMP999"}}, # Non-existent
            headers={"Authorization": f"Bearer {token}"}
        )
    
    # Changed from 404 to 403 for enumeration protection (BUG-006)
    assert response.status_code == 403
    error = response.json()
    assert error["error_code"] == "UNAUTHORIZED"
    assert "Access denied" in error["message"]
