import pytest
import time
from src.domain.services.policy_engine import PolicyEngine
from src.domain.entities.policy import AccessPolicy, PolicyRule, PrincipalDefinition, Environment

# Sample Policy Data
@pytest.fixture
def sample_policy_data():
    return {
        "version": "1.0",
        "metadata": {
            "last_reviewed": "2026-01-26",
            "reviewed_by": "test",
            "ticket": "TEST-1"
        },
        "principals": {
            "admin": {
                "type": "HUMAN",
                "okta_group": "admins"
            },
            "worker": {
                "type": "MACHINE",
                "okta_subject": "worker-1"
            }
        },
        "capability_groups": {
            "all_workday": ["workday.*"]
        },
        "policies": [
            {
                "name": "admin-access",
                "principal": "admin",
                "capabilities": "all_workday",
                "environments": ["local", "dev"],
                "effect": "ALLOW",
                "audit": "VERBOSE"
            },
            {
                "name": "worker-access",
                "principal": "worker",
                "capabilities": ["workday.get_employee"],
                "environments": ["prod"],
                "effect": "ALLOW",
                "audit": "BASIC"
            }
        ]
    }

@pytest.fixture
def policy_with_conditions():
    data = {
        "version": "1.0",
        "policies": [
            {
                "name": "mfa-required-policy",
                "principal": "human-user",
                "capabilities": ["sensitive.action"],
                "environments": ["prod"],
                "effect": "ALLOW",
                "conditions": {
                    "require_mfa": True
                }
            },
            {
                "name": "short-ttl-policy",
                "principal": "ai-agent",
                "capabilities": ["quick.action"],
                "environments": ["prod"],
                "effect": "ALLOW",
                "conditions": {
                    "max_ttl_seconds": 300
                }
            }
        ],
        "principals": {
            "human-user": { "type": "HUMAN" },
            "ai-agent": { "type": "AI_AGENT" }
        }
    }
    return AccessPolicy(**data)

def test_policy_engine_allow_exact_match(sample_policy_data):
    # Mock loader returning the sample policy
    policy = AccessPolicy(**sample_policy_data)
    engine = PolicyEngine(policy)
    
    # Simulate a principal matching 'worker' in 'prod' accessing allowed capability
    result = engine.evaluate(
        principal_id="worker-1",
        principal_groups=[],
        principal_type="MACHINE",
        capability="workday.get_employee",
        environment="prod"
    )
    assert result.allowed is True
    assert result.policy_name == "worker-access"

def test_policy_engine_deny_environment_mismatch(sample_policy_data):
    policy = AccessPolicy(**sample_policy_data)
    engine = PolicyEngine(policy)
    
    # Worker trying to access in 'dev' (only allowed in 'prod')
    result = engine.evaluate(
        principal_id="worker-1",
        principal_groups=[],
        principal_type="MACHINE",
        capability="workday.get_employee",
        environment="dev"
    )
    assert result.allowed is False

def test_policy_engine_allow_wildcard_group(sample_policy_data):
    policy = AccessPolicy(**sample_policy_data)
    engine = PolicyEngine(policy)
    
    # Admin matching via group accessing wildcard capability
    result = engine.evaluate(
        principal_id="some-admin",
        principal_groups=["admins"],
        principal_type="HUMAN",
        capability="workday.any_action",
        environment="local"
    )
    assert result.allowed is True
    assert result.policy_name == "admin-access"

def test_policy_engine_deny_unlisted_capability(sample_policy_data):
    policy = AccessPolicy(**sample_policy_data)
    engine = PolicyEngine(policy)
    
    # Worker trying to access unlisted capability
    result = engine.evaluate(
        principal_id="worker-1",
        principal_groups=[],
        principal_type="MACHINE",
        capability="workday.delete_employee",
        environment="prod"
    )
    assert result.allowed is False

def test_evaluate_enforces_mfa_condition_fail(policy_with_conditions):
    engine = PolicyEngine(policy_with_conditions)
    
    # Fails because mfa_verified defaults to False
    result = engine.evaluate(
        principal_id="user1",
        principal_groups=[],
        principal_type="HUMAN",
        capability="sensitive.action",
        environment="prod"
    )
    
    assert result.allowed is False

def test_evaluate_enforces_mfa_condition_pass(policy_with_conditions):
    engine = PolicyEngine(policy_with_conditions)
    
    # Passes because mfa_verified is True
    result = engine.evaluate(
        principal_id="user1",
        principal_groups=[],
        principal_type="HUMAN",
        capability="sensitive.action",
        environment="prod",
        mfa_verified=True
    )
    
    assert result.allowed is True

def test_evaluate_enforces_ttl_condition_fail(policy_with_conditions):
    engine = PolicyEngine(policy_with_conditions)
    
    now = int(time.time())
    # TTL = 3600 (1 hour) > 300
    result = engine.evaluate(
        principal_id="agent1",
        principal_groups=[],
        principal_type="AI_AGENT",
        capability="quick.action",
        environment="prod",
        token_issued_at=now,
        token_expires_at=now + 3600
    )
    
    assert result.allowed is False

def test_evaluate_enforces_ttl_condition_pass(policy_with_conditions):
    engine = PolicyEngine(policy_with_conditions)
    
    now = int(time.time())
    # TTL = 100 <= 300
    result = engine.evaluate(
        principal_id="agent1",
        principal_groups=[],
        principal_type="AI_AGENT",
        capability="quick.action",
        environment="prod",
        token_issued_at=now,
        token_expires_at=now + 100
    )
    
    assert result.allowed is True