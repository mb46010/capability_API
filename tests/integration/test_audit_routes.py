import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
import json
import os
from pathlib import Path

@pytest.mark.asyncio
async def test_get_recent_audit_logs_success(tmp_path, admin_token):
    # Create a dummy audit log file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "audit.jsonl"
    
    event = {"event_type": "test_event", "actor": "admin"}
    with open(log_file, "w") as f:
        f.write(json.dumps(event) + "\n")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 1
    assert data["events"][0]["event_type"] == "test_event"

@pytest.mark.asyncio
async def test_get_recent_audit_logs_forbidden(user_token):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 403
