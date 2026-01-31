import pytest
from unittest.mock import MagicMock
from src.domain.services.policy_engine import PolicyEngine
from src.domain.entities.policy import PolicyRule, PolicyConditions, AccessPolicy

@pytest.fixture
def policy_engine():
    mock_policy = MagicMock(spec=AccessPolicy)
    return PolicyEngine(policy=mock_policy)

def test_policy_enforces_required_scope(policy_engine):
    """T017: Verify policy engine enforces required_scope condition."""
    # policy_engine is yielded by fixture
    engine = policy_engine
    
    # Define a rule requiring 'mcp:use' scope
    rule = PolicyRule(
        name="test-scope-rule",
        principal="test-user",
        capabilities=["test.capability"],
        environments=["local"],
        effect="ALLOW",
        conditions=PolicyConditions(required_scope="mcp:use")
    )
    
    # Case 1: Token HAS the scope -> ALLOW
    token_scopes_valid = ["openid", "mcp:use"]
    result_valid = engine._evaluate_conditions(
        rule=rule, 
        mfa_verified=False, 
        token_issued_at=None, 
        token_expires_at=None, 
        request_ip="127.0.0.1",
        token_scopes=token_scopes_valid
    )
    assert result_valid is True
    
    # Case 2: Token MISSING the scope -> DENY
    token_scopes_invalid = ["openid", "api:read"]
    result_invalid = engine._evaluate_conditions(
        rule=rule,
        mfa_verified=False,
        token_issued_at=None,
        token_expires_at=None,
        request_ip="127.0.0.1",
        token_scopes=token_scopes_invalid
    )
    assert result_invalid is False

    # Case 3: Token has no scopes -> DENY
    token_scopes_empty = []
    result_empty = engine._evaluate_conditions(
        rule=rule,
        mfa_verified=False,
        token_issued_at=None,
        token_expires_at=None,
        request_ip="127.0.0.1",
        token_scopes=token_scopes_empty
    )
    assert result_empty is False

def test_policy_enforces_max_auth_age(policy_engine):
    """T024: Verify policy engine enforces max_auth_age_seconds."""
    engine = policy_engine
    
    # Rule requiring recent auth (e.g., 300s = 5m)
    rule = PolicyRule(
        name="test-freshness-rule",
        principal="test-user",
        capabilities=["test.sensitive"],
        environments=["local"],
        effect="ALLOW",
        conditions=PolicyConditions(max_auth_age_seconds=300)
    )
    
    current_time = 1000
    
    # Case 1: Fresh auth (100s ago) -> ALLOW
    auth_time_fresh = current_time - 100
    result_fresh = engine._evaluate_conditions(
        rule=rule,
        mfa_verified=False,
        token_issued_at=None,
        token_expires_at=None,
        request_ip="127.0.0.1",
        auth_time=auth_time_fresh,
        current_time_override=current_time
    )
    assert result_fresh is True
    
    # Case 2: Stale auth (400s ago) -> DENY
    auth_time_stale = current_time - 400
    result_stale = engine._evaluate_conditions(
        rule=rule,
        mfa_verified=False,
        token_issued_at=None,
        token_expires_at=None,
        request_ip="127.0.0.1",
        auth_time=auth_time_stale,
        current_time_override=current_time
    )
    assert result_stale is False

def test_freshness_check_handles_missing_auth_time(policy_engine):
    """T025: Verify missing auth_time results in denial if max_auth_age_seconds is set."""
    engine = policy_engine
    rule = PolicyRule(
        name="test-freshness-rule",
        principal="test-user",
        capabilities=["test.sensitive"],
        environments=["local"],
        effect="ALLOW",
        conditions=PolicyConditions(max_auth_age_seconds=300)
    )
    
    # Missing auth_time -> DENY
    result = engine._evaluate_conditions(
        rule=rule,
        mfa_verified=False,
        token_issued_at=None,
        token_expires_at=None,
        request_ip="127.0.0.1",
        auth_time=None
    )
    assert result is False
