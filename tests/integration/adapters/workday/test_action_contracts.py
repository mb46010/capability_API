import pytest
from src.api.dependencies import provider

@pytest.mark.asyncio
async def test_contract_get_employee(async_client):
    """US1: get_employee matches ActionResponse contract."""
    token = provider.issue_token(subject="admin@local.test", groups=["hr-platform-admins"])
    
    response = await async_client.post(
        "/actions/workday.hcm/get_employee",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "meta" in data
    assert data["data"]["employee_id"] == "EMP001"
    assert "provenance" in data["meta"]

@pytest.mark.asyncio
async def test_contract_get_balance(async_client):
    """US1: get_balance matches ActionResponse contract."""
    token = provider.issue_token(subject="EMP001", groups=["employees"])
    
    response = await async_client.post(
        "/actions/workday.time/get_balance",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"]["balances"], list)
    assert data["data"]["employee_id"] == "EMP001"

@pytest.mark.asyncio
async def test_contract_request_time_off(async_client):
    """US2: request matches ActionResponse contract (Mutation)."""
    token = provider.issue_token(subject="EMP001", groups=["employees"])
    
    response = await async_client.post(
        "/actions/workday.time/request",
        json={"parameters": {
            "employee_id": "EMP001",
            "type": "PTO",
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "hours": 8
        }},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "PENDING"
    assert data["data"]["request_id"].startswith("TOR-")

@pytest.mark.asyncio
async def test_contract_update_contact_info(async_client):
    """US2: update_contact_info matches ActionResponse contract."""
    token = provider.issue_token(
        subject="EMP001", 
        groups=["employees"],
        additional_claims={"amr": ["mfa", "pwd"]} # MFA required
    )
    
    response = await async_client.post(
        "/actions/workday.hcm/update_contact_info",
        json={"parameters": {
            "employee_id": "EMP001",
            "updates": {"personal_email": "new@example.com"}
        }},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "APPLIED"
    assert "transaction_id" in data["data"]

@pytest.mark.asyncio
async def test_contract_get_compensation_security(async_client):
    """US3: get_compensation requires MFA claim."""
    # No MFA
    token = provider.issue_token(subject="EMP001", groups=["employees"])
    
    response = await async_client.post(
        "/actions/workday.payroll/get_compensation",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403 # PolicyEngine or Service checks it
    # Note: If checking in Service, it might return 400/403 with MFA_REQUIRED
    # If checking in Policy, it returns 403 Forbidden.
    
@pytest.mark.asyncio
async def test_contract_approve_time_off(async_client):
    """US3: approve matches ActionResponse contract (Manager)."""
    # 1. Create a request first
    token_emp = provider.issue_token(subject="EMP001", groups=["employees"])
    req_resp = await async_client.post(
        "/actions/workday.time/request",
        json={"parameters": {
            "employee_id": "EMP001", "type": "PTO", 
            "start_date": "2026-06-01", "end_date": "2026-06-02", "hours": 8
        }},
        headers={"Authorization": f"Bearer {token_emp}"}
    )
    assert req_resp.status_code == 200, f"Request failed: {req_resp.text}"
    request_id = req_resp.json()["data"]["request_id"]
    
    # 2. Approve as Manager (EMP042 is manager of EMP001 in fixtures)
    token_mgr = provider.issue_token(
        subject="EMP042", 
        groups=["people-managers"],
        additional_claims={"amr": ["mfa", "pwd"]}
    )

    
    response = await async_client.post(
        "/actions/workday.time/approve",
        json={"parameters": {"request_id": request_id}},
        headers={"Authorization": f"Bearer {token_mgr}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["status"] == "APPROVED"
    assert data["data"]["approved_by"] == "EMP042"

@pytest.mark.asyncio
async def test_contract_unauthorized_self_service(async_client):
    """Verify 403 when trying to access another's balance."""
    token = provider.issue_token(subject="EMP002", groups=["employees"])
    
    response = await async_client.post(
        "/actions/workday.time/get_balance",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_contract_mfa_required_compensation(async_client):
    """Verify 403/MFA error when claim is missing."""
    token = provider.issue_token(subject="EMP001", groups=["employees"])
    
    response = await async_client.post(
        "/actions/workday.payroll/get_compensation",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # The WorkdayPayrollService raises WorkdayError("MFA_REQUIRED") 
    # which main.py maps to an appropriate status code (likely 403 or 401).
    assert response.status_code in [401, 403]
