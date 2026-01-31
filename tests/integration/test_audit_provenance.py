import pytest
import json
from src.adapters.filesystem.logger import JSONLLogger

@pytest.mark.asyncio
async def test_audit_log_contains_provenance_fields(tmp_path):
    """T030: Verify audit log entries include provenance metadata."""
    log_file = tmp_path / "audit.jsonl"
    logger = JSONLLogger(log_path=str(log_file))
    
    token_claims = {        "jti": "token-123",
        "scope": ["mcp:use"],
        "acting_as": "mcp-server",
        "original_token_id": "user-token-456",
        "iat": 1700000000,
        "exp": 1700000300,
        "auth_time": 1700000000
    }
    
    logger.log_event("test_action", {"foo": "bar"}, actor="test-actor", token_claims=token_claims)
    
    # Read back
    with open(log_file, "r") as f:
        line = f.readline()
        entry = json.loads(line)
        
    assert entry["event_type"] == "test_action"
    assert entry["acting_through"] == "mcp-server"
    assert entry["token_type"] == "exchanged"
    assert entry["original_token_id"] == "user-token-456"
    assert entry["token_scope"] == ["mcp:use"]
    assert "token_ttl_seconds" in entry
    assert entry["token_ttl_seconds"] == 300
    assert "auth_age_seconds" in entry