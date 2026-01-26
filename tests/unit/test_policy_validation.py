import pytest
from src.domain.entities.policy import AccessPolicy

def test_policy_validation_success():
    data = {
        "version": "1.0",
        "principals": {
            "admin": {"type": "HUMAN"}
        },
        "capability_groups": {
            "all": ["*"]
        },
        "policies": [
            {
                "name": "policy1",
                "principal": "admin",
                "capabilities": "all",
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    policy = AccessPolicy(**data)
    assert len(policy.validate_references()) == 0

def test_policy_validation_missing_principal():
    data = {
        "version": "1.0",
        "principals": {
            "admin": {"type": "HUMAN"}
        },
        "policies": [
            {
                "name": "policy1",
                "principal": "unknown_user",
                "capabilities": ["*"],
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    policy = AccessPolicy(**data)
    errors = policy.validate_references()
    assert len(errors) == 1
    assert "undefined principal 'unknown_user'" in errors[0]

def test_policy_validation_missing_capability_group():
    data = {
        "version": "1.0",
        "principals": {
            "admin": {"type": "HUMAN"}
        },
        "policies": [
            {
                "name": "policy1",
                "principal": "admin",
                "capabilities": "unknown_group",
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    policy = AccessPolicy(**data)
    errors = policy.validate_references()
    assert len(errors) == 1
    assert "undefined capability group 'unknown_group'" in errors[0]

def test_policy_validation_duplicate_name():
    data = {
        "version": "1.0",
        "principals": {
            "admin": {"type": "HUMAN"}
        },
        "policies": [
            {
                "name": "policy1",
                "principal": "admin",
                "capabilities": ["*"],
                "environments": ["local"],
                "effect": "ALLOW"
            },
            {
                "name": "policy1",
                "principal": "admin",
                "capabilities": ["*"],
                "environments": ["dev"],
                "effect": "ALLOW"
            }
        ]
    }
    policy = AccessPolicy(**data)
    errors = policy.validate_references()
    assert len(errors) == 1
    assert "Duplicate policy name found: 'policy1'" in errors[0]
