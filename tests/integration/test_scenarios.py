import pytest
import time
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider

# ---------------------------------------------------------------------------
# Scenario 1: Employee Lookup (Action)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_1_1_admin_full_access(async_client):
    """Test 1.1: Admin Full Access - Gets full record."""
    # Given: Admin user
    token = provider.issue_token(
        subject="admin@local.test", 
        groups=["hr-platform-admins"], 
        principal_type="HUMAN",
        additional_claims={"amr": ["mfa", "pwd"]} # MFA required by policy
    )
    
    response = await async_client.post(
        "/actions/workday.hcm/get_employee_full",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["employee_id"] == "EMP001"
    # national_id_last_four is sensitive PII
    assert "national_id_last_four" in data
    assert response.json()["meta"]["provenance"]["actor"] == "admin@local.test"

@pytest.mark.asyncio
async def test_1_2_ai_agent_limited_access(async_client):
    """Test 1.2: AI Agent Limited Access - Gets limited record."""
    # Given: AI Agent
    token = provider.issue_token(
        subject="agent-assistant@local.test", 
        principal_type="AI_AGENT",
        ttl_seconds=300
    )
    
    response = await async_client.post(
        "/actions/workday.hcm/get_employee",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["employee_id"] == "EMP001"
    # AI Agents should not see sensitive fields even if they were in the response
    # (though get_employee doesn't have them anyway)
    assert "national_id_last_four" not in data

@pytest.mark.asyncio
async def test_1_3_ai_agent_denied_compensation(async_client):
    """Test 1.3: AI Agent Denied Compensation Data."""
    token = provider.issue_token(
        subject="agent-assistant@local.test", 
        principal_type="AI_AGENT",
        ttl_seconds=300
    )
    
    response = await async_client.post(
        "/actions/workday.payroll/get_compensation",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_1_4_unauthorized_user_denied(async_client):
    """Test 1.4: Unauthorized User Denied."""
    token = provider.issue_token(
        subject="unauthorized@local.test", 
        principal_type="HUMAN"
    )
    
    response = await async_client.post(
        "/actions/workday.hcm/get_employee",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_1_5_machine_workflow_scoped_access(async_client, monkeypatch):
    """Test 1.5: Machine Workflow Scoped Access."""
    # Patch the settings object directly (env var won't affect already-loaded settings)
    from src.lib.config_validator import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "dev")

    token = provider.issue_token(
        subject="svc-workflow@local.test",
        principal_type="MACHINE"
    )

    # Allowed: get_employee_full
    resp1 = await async_client.post(
        "/actions/workday.hcm/get_employee_full",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp1.status_code == 200
    assert "national_id_last_four" in resp1.json()["data"]

    # Denied: terminate_employee (not in policy for MACHINE in dev environment)
    resp2 = await async_client.post(
        "/actions/workday.hcm/terminate_employee",
        json={"parameters": {"employee_id": "EMP001", "termination_date": "2026-12-31", "reason_code": "VOLUNTARY_RESIGNATION"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp2.status_code == 403

# ---------------------------------------------------------------------------
# Scenario 2: Onboarding Flow (Flow)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_2_1_machine_triggers_onboarding(async_client):
    """Test 2.1: Machine Workflow Triggers Onboarding."""
    token = provider.issue_token(
        subject="svc-workflow@local.test", 
        principal_type="MACHINE"
    )
    
    response = await async_client.post(
        "/flows/hr/onboarding",
        json={"parameters": {"employee_name": "Jane Doe"}},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 202
    flow_id = response.json()["flow_id"]
    
    # Check status
    status_resp = await async_client.get(
        f"/flows/{flow_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "RUNNING"

@pytest.mark.asyncio
async def test_2_2_ai_agent_denied_flow(async_client):
    """Test 2.2: AI Agent Denied Flow Trigger."""
    token = provider.issue_token(
        subject="agent-assistant@local.test", 
        principal_type="AI_AGENT",
        ttl_seconds=300
    )
    
    response = await async_client.post(
        "/flows/hr/onboarding",
        json={"parameters": {}},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403

# ---------------------------------------------------------------------------
# Scenario 3: Authentication & Token Lifecycle
# ---------------------------------------------------------------------------

@pytest.mark.asyncio

async def test_3_2_expired_token_rejected(async_client):

    """Test 3.2: Expired Token Rejected."""

    # Issue token with negative TTL

    token = provider.issue_token(subject="admin@local.test", ttl_seconds=-10)

    

    response = await async_client.post(

        "/actions/workday.hcm/get_employee",

        json={"parameters": {"employee_id": "EMP001"}},

        headers={"Authorization": f"Bearer {token}"}

    )

    

    # Should be 401

    assert response.status_code == 401

    # Check standardized error code

    assert response.json()["error_code"] == "UNAUTHORIZED"

    assert response.json()["message"] == "token_expired"



@pytest.mark.asyncio

async def test_3_4_ai_agent_ttl_enforcement(async_client):

    """Test 3.4: AI Agent TTL Enforcement via Policy."""

    # Policy says max_ttl_seconds: 300

    # Issue a token valid for 1 hour (3600s)

    token = provider.issue_token(

        subject="agent-assistant@local.test", 

        principal_type="AI_AGENT", 

        ttl_seconds=3600

    )

    

    # Use it. Policy engine checks (exp - iat) <= 300.

    # 3600 > 300, so should be denied by policy.

    response = await async_client.post(

        "/actions/workday.hcm/get_employee",

        json={"parameters": {"employee_id": "EMP001"}},

        headers={"Authorization": f"Bearer {token}"}

    )

    

    assert response.status_code == 403



@pytest.mark.asyncio

async def test_3_5_mfa_required_but_missing(async_client):

    """Test 3.5: MFA Required But Not Present."""

    # Admin policy requires MFA

    token = provider.issue_token(

        subject="admin@local.test", 

        groups=["hr-platform-admins"],

        principal_type="HUMAN",

        additional_claims={"amr": ["pwd"]} # No MFA

    )

    

    response = await async_client.post(

        "/actions/workday.hcm/get_employee",

        json={"parameters": {"employee_id": "EMP001"}},

        headers={"Authorization": f"Bearer {token}"}

    )

    

    assert response.status_code == 403



# ---------------------------------------------------------------------------

# Scenario 5: Edge Cases

# ---------------------------------------------------------------------------



@pytest.mark.asyncio

async def test_5_1_nonexistent_employee(async_client):

    """Test 5.1: Nonexistent Employee."""

    token = provider.issue_token(

        subject="admin@local.test", 

        groups=["hr-platform-admins"], 

        additional_claims={"amr": ["mfa", "pwd"]}

    )

    

    response = await async_client.post(

        "/actions/workday.hcm/get_employee",

        json={"parameters": {"employee_id": "DOES_NOT_EXIST"}},

        headers={"Authorization": f"Bearer {token}"}

    )

    

    assert response.status_code == 404

    assert response.json()["error_code"] == "EMPLOYEE_NOT_FOUND"



@pytest.mark.asyncio

async def test_5_2_connector_timeout(async_client):

    """Test 5.2: Connector Timeout (Simulated)."""

    token = provider.issue_token(

        subject="admin@local.test", 

        groups=["hr-platform-admins"], 

        additional_claims={"amr": ["mfa", "pwd"]}

    )

    

    # Register a dependency override to simulate failure

    from src.api.dependencies import get_connector

    from src.adapters.workday.client import WorkdaySimulator

    from src.adapters.workday.config import WorkdaySimulationConfig

    

    config = WorkdaySimulationConfig(timeout_rate=1.0) # 100% timeout

    simulator = WorkdaySimulator(config)

    

    app.dependency_overrides[get_connector] = lambda: simulator

    

    try:

        response = await async_client.post(

            "/actions/workday.hcm/get_employee",

            json={"parameters": {"employee_id": "EMP001"}},

            headers={"Authorization": f"Bearer {token}"}

        )

        

        assert response.status_code == 504

        assert response.json()["error_code"] == "CONNECTOR_TIMEOUT"

    finally:

        app.dependency_overrides.clear()
