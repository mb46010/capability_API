import pytest
import yaml
import tempfile
from pathlib import Path
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter

@pytest.fixture
def temp_files():
    # Create a registry
    registry_data = {
        "version": "1.0",
        "metadata": {"last_updated": "x", "owner": "x", "description": "x"},
        "capabilities": [
            {"id": "workday.hcm.get_employee", "name": "n", "domain": "d", "type": "action", "sensitivity": "low"},
            {"id": "workday.time.get_balance", "name": "n", "domain": "d", "type": "action", "sensitivity": "low"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_reg.yaml', delete=False) as rf:
        yaml.dump(registry_data, rf)
        reg_path = rf.name
        
    yield reg_path
    Path(reg_path).unlink()

def test_valid_policy_loads(temp_files):
    reg_path = temp_files
    policy_data = {
        "version": "1.0",
        "policies": [
            {
                "name": "test-rule",
                "principal": {"type": "HUMAN", "okta_group": "test"},
                "capabilities": ["workday.hcm.get_employee"],
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_pol.yaml', delete=False) as pf:
        yaml.dump(policy_data, pf)
        pol_path = pf.name
        
    loader = FilePolicyLoaderAdapter(pol_path, registry_path=reg_path)
    policy = loader.load_policy()
    assert len(policy.policies) == 1
    
    Path(pol_path).unlink()

def test_invalid_capability_fails(temp_files):
    reg_path = temp_files
    policy_data = {
        "version": "1.0",
        "policies": [
            {
                "name": "test-rule",
                "principal": {"type": "HUMAN", "okta_group": "test"},
                "capabilities": ["workday.hcm.get_employe"], # Typo
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_pol.yaml', delete=False) as pf:
        yaml.dump(policy_data, pf)
        pol_path = pf.name
        
    loader = FilePolicyLoaderAdapter(pol_path, registry_path=reg_path)
    with pytest.raises(ValueError, match="Policy capability validation failed"):
        loader.load_policy()
        
    Path(pol_path).unlink()

def test_wildcard_no_match_fails(temp_files):
    reg_path = temp_files
    policy_data = {
        "version": "1.0",
        "policies": [
            {
                "name": "test-rule",
                "principal": {"type": "HUMAN", "okta_group": "test"},
                "capabilities": ["unknown.*"],
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='_pol.yaml', delete=False) as pf:
        yaml.dump(policy_data, pf)
        pol_path = pf.name
        
    loader = FilePolicyLoaderAdapter(pol_path, registry_path=reg_path)
    with pytest.raises(ValueError, match="matches no capabilities"):
        loader.load_policy()
        
    Path(pol_path).unlink()
