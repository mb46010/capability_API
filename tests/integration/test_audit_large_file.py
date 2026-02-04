import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
import json
from pathlib import Path
from collections import deque

@pytest.mark.asyncio
async def test_get_recent_audit_logs_large_file(tmp_path, admin_token, monkeypatch):
    # Setup a large mock audit log file
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "audit.jsonl"
    
    # Create 1000 lines
    lines = []
    for i in range(1000):
        event = {"event_type": f"test_event_{i}", "index": i}
        lines.append(json.dumps(event) + "\n")
    
    with open(log_file, "w") as f:
        f.writelines(lines)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Test default limit (20)
        response = await ac.get(
            "/audit/recent",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 20
        # Since I added .reverse(), index should be 999, 998, ...
        assert data["events"][0]["index"] == 999
        assert data["events"][19]["index"] == 980

        # Test custom limit within bounds
        response = await ac.get(
            "/audit/recent?limit=50",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 50
        assert data["events"][0]["index"] == 999
        assert data["events"][49]["index"] == 950

        # Test limit exceeding MAX_AUDIT_LOG_LIMIT (500)
        response = await ac.get(
            "/audit/recent?limit=1000",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 500 # Clamped to 500
        assert data["events"][0]["index"] == 999
        assert data["events"][499]["index"] == 500

    # Cleanup log file to avoid affecting other tests
    if log_file.exists():
        log_file.unlink()