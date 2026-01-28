import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import provider
import json
import os
from pathlib import Path

@pytest.mark.asyncio
async def test_get_recent_audit_logs_success(tmp_path):
    # Create a dummy audit log file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "audit.jsonl"
    
    event = {"event_type": "test_event", "actor": "admin"}
    with open(log_file, "w") as f:
        f.write(json.dumps(event) + "\n")

    # Issue a token for an admin
    token = provider.issue_token(
        subject="admin@local.test",
        principal_type="HUMAN",
        groups=["hr-platform-admins"]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["events"][0]["event_type"] == "test_event"

@pytest.mark.asyncio
async def test_get_recent_audit_logs_forbidden():
    # Issue a token for a non-admin
    token = provider.issue_token(
        subject="user@local.test",
        principal_type="HUMAN",
        groups=["employees"]
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 403
