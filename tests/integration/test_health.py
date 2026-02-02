import pytest
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_health_check_success():
    """Test that the health check returns 200 and the expected structure."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "ok"
    assert "version" in data
    assert "environment" in data
    assert "response_time_ms" in data
    assert "checks" in data
    
    checks = data["checks"]
    assert "policy_engine" in checks
    assert checks["policy_engine"]["status"] == "ok"
    assert "policy_count" in checks["policy_engine"]
    assert "response_time_ms" in checks["policy_engine"]
    
    assert "connector" in checks
    assert checks["connector"]["status"] == "ok"
    assert "type" in checks["connector"]
    assert "employee_count" in checks["connector"]
    assert "response_time_ms" in checks["connector"]
