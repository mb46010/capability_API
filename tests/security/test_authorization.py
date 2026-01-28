"""
Demonstrate that authorization is enforced at multiple layers

run: pytest tests/security/ -v --tb=short

"""

import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


class TestSecurityBoundaries:
    """Demonstrate that authorization is enforced at multiple layers"""

    def test_ai_agent_cannot_see_salary(self):
        """AI agents are denied access to compensation data"""
        # Get AI agent token
        token_resp = client.post(
            "/test/tokens", json={"subject": "agent-assistant@local.test"}
        )
        token = token_resp.json()["access_token"]

        # Attempt to access compensation
        resp = client.post(
            "/actions/workday.payroll/get_compensation",
            headers={"Authorization": f"Bearer {token}"},
            json={"parameters": {"employee_id": "EMP001"}},
        )

        # Should be denied at policy layer
        assert resp.status_code == 403
        assert "denied" in resp.json()["message"].lower()

    def test_ai_agent_sees_filtered_employee_data(self):
        """AI agents see limited employee fields"""
        # Get AI agent token
        token_resp = client.post(
            "/test/tokens", json={"subject": "agent-assistant@local.test"}
        )
        token = token_resp.json()["access_token"]

        # Access employee data (allowed)
        resp = client.post(
            "/actions/workday.hcm/get_employee",
            headers={"Authorization": f"Bearer {token}"},
            json={"parameters": {"employee_id": "EMP001"}},
        )

        assert resp.status_code == 200
        data = resp.json()["data"]

        # Verify sensitive fields are filtered
        assert "employee_id" in data  # Should have
        assert "name" in data  # Should have
        assert "salary" not in data  # Should NOT have
        assert "ssn_last_four" not in data  # Should NOT have

    def test_user_cannot_access_others_data(self):
        """Users can only access their own data"""
        # Get token for EMP001
        token_resp = client.post("/test/tokens", json={"subject": "EMP001"})
        token = token_resp.json()["access_token"]

        # Try to access EMP042's data
        resp = client.post(
            "/actions/workday.hcm/get_employee",
            headers={"Authorization": f"Bearer {token}"},
            json={"parameters": {"employee_id": "EMP042"}},
        )

        # Should be denied at service layer (defense in depth)
        assert resp.status_code in [403, 404]

    def test_mfa_required_for_compensation(self):
        """Compensation access requires MFA"""
        # Get token WITHOUT MFA
        token_resp = client.post(
            "/test/tokens",
            json={
                "subject": "EMP001"
                # No MFA claim
            },
        )
        token = token_resp.json()["access_token"]

        resp = client.post(
            "/actions/workday.payroll/get_compensation",
            headers={"Authorization": f"Bearer {token}"},
            json={"parameters": {"employee_id": "EMP001"}},
        )

        # Should be denied at policy layer OR service layer
        assert resp.status_code in [401, 403]
