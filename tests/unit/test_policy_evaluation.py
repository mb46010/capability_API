import pytest
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter

def test_specific_principal_overrides_type():
    """Specific principal policies should take precedence over type-based policies"""
    loader = FilePolicyLoaderAdapter("config/policy-workday.yaml")
    policy = loader.load_policy()
    engine = PolicyEngine(policy)
    
    # Test 1: Specific agent (hr_assistant) should get allowed for its capabilities
    # hr_assistant has workday_hcm_read_public which includes workday.hcm.get_employee
    # Providing token timestamps to satisfy TTL condition (max 300s)
    result = engine.evaluate(
        principal_id="agent-assistant@local.test",
        principal_groups=[],
        principal_type="AI_AGENT",
        capability="workday.hcm.get_employee",
        environment="local",
        token_issued_at=1000,
        token_expires_at=1100  # TTL 100 < 300
    )
    assert result.allowed == True  # Has this specific capability
    
    # Test 2: Specific agent (hr_assistant) should be denied for capabilities it doesn't have
    # workday.hcm.terminate_employee is in workday_hcm_write, which hr_assistant doesn't have
    result = engine.evaluate(
        principal_id="agent-assistant@local.test",
        principal_groups=[],
        principal_type="AI_AGENT",
        capability="workday.hcm.terminate_employee",
        environment="local",
        token_issued_at=1000,
        token_expires_at=1100
    )
    assert result.allowed == False  # Should be denied
    
    # Test 3: Unknown AI agent should NOT match specific policies (hr_assistant's policies)
    # Since there are no generic AI_AGENT policies in policy-workday.yaml, this should be False
    result = engine.evaluate(
        principal_id="agent-unknown@local.test",
        principal_groups=[],
        principal_type="AI_AGENT",
        capability="workday.hcm.get_employee",
        environment="local",
        token_issued_at=1000,
        token_expires_at=1100
    )
    assert result.allowed == False
