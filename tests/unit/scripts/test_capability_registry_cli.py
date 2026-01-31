import pytest
import subprocess
import yaml
import tempfile
import os
from pathlib import Path

@pytest.fixture
def temp_registry():
    data = {
        "version": "1.0",
        "metadata": {"last_updated": "x", "owner": "x", "description": "x"},
        "capabilities": [
            {"id": "test.action", "name": "Test Action", "domain": "test", "type": "action", "sensitivity": "low"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(data, f)
        path = f.name
    yield path
    if Path(path).exists():
        Path(path).unlink()

def test_cli_list(temp_registry):
    result = subprocess.run(
        ["python3", "scripts/capability-registry", "--registry", temp_registry, "list", "--format", "simple"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "test.action" in result.stdout

def test_cli_validate(temp_registry):
    result = subprocess.run(
        ["python3", "scripts/capability-registry", "--registry", temp_registry, "validate"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Registry is valid" in result.stdout

def test_cli_check_policy_valid(temp_registry):
    policy_data = {
        "version": "1.0",
        "policies": [
            {
                "name": "rule",
                "principal": {"type": "HUMAN", "okta_group": "g"},
                "capabilities": ["test.action"],
                "environments": ["local"],
                "effect": "ALLOW"
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as pf:
        yaml.dump(policy_data, pf)
        pol_path = pf.name
        
    result = subprocess.run(
        ["python3", "scripts/capability-registry", "--registry", temp_registry, "check-policy", pol_path],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Policy is valid" in result.stdout
    if Path(pol_path).exists():
        Path(pol_path).unlink()

def test_cli_check_policy_invalid(temp_registry):
    policy_data = {
        "version": "1.0",
        "policies": [
            {"name": "rule", "principal": {"type": "HUMAN"}, "capabilities": ["wrong.id"], "environments": ["local"], "effect": "ALLOW"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as pf:
        yaml.dump(policy_data, pf)
        pol_path = pf.name
        
    result = subprocess.run(
        ["python3", "scripts/capability-registry", "--registry", temp_registry, "check-policy", pol_path],
        capture_output=True, text=True
    )
    assert result.returncode == 1
    assert "Policy validation failed" in result.stdout
    if Path(pol_path).exists():
        Path(pol_path).unlink()