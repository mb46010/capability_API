import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
import json
from pathlib import Path
from src.lib.config_validator import settings

@pytest.mark.asyncio
async def test_audit_logs_custom_path(tmp_path, admin_token, monkeypatch):
    # 1. Setup a custom log path
    custom_log_dir = tmp_path / "custom_logs"
    custom_log_dir.mkdir()
    custom_log_file = custom_log_dir / "custom_audit.jsonl"
    
    # Write a test event
    event = {"event_type": "custom_path_event", "actor": "admin"}
    with open(custom_log_file, "w") as f:
        f.write(json.dumps(event) + "\n")

    # 2. Mock settings.AUDIT_LOG_PATH
    monkeypatch.setattr(settings, "AUDIT_LOG_PATH", str(custom_log_file))

    # 3. Call the API
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

    # 4. Verify
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert data["events"][0]["event_type"] == "custom_path_event"
    # The note should not contain "Log file not found"
    assert "Log file not found" not in data.get("note", "")