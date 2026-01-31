import pytest
import yaml
import tempfile
from pathlib import Path
from src.domain.services.capability_registry import CapabilityRegistryService
from src.domain.entities.capability import CapabilityType

@pytest.fixture
def temp_registry_file():
    data = {
        "version": "1.0",
        "metadata": {
            "last_updated": "2026-01-31",
            "owner": "test",
            "description": "test"
        },
        "capabilities": [
            {
                "id": "workday.hcm.get_employee",
                "name": "Get Employee",
                "domain": "workday.hcm",
                "type": "action",
                "sensitivity": "medium",
                "tags": ["hcm"]
            },
            {
                "id": "workday.time.get_balance",
                "name": "Get Balance",
                "domain": "workday.time",
                "type": "action",
                "sensitivity": "low",
                "tags": ["time"]
            },
            {
                "id": "workday.payroll.get_pay_statement",
                "name": "Get Pay Statement",
                "domain": "workday.payroll",
                "type": "action",
                "sensitivity": "critical",
                "requires_mfa": True,
                "deprecated": True
            }
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(data, f)
        temp_path = f.name
    
    yield temp_path
    Path(temp_path).unlink()

def test_load_registry(temp_registry_file):
    service = CapabilityRegistryService(temp_registry_file)
    assert len(service.get_all()) == 3
    assert service.exists("workday.hcm.get_employee")
    assert not service.exists("invalid.id")

def test_get_by_id(temp_registry_file):
    service = CapabilityRegistryService(temp_registry_file)
    cap = service.get("workday.hcm.get_employee")
    assert cap.name == "Get Employee"
    assert cap.domain == "workday.hcm"

def test_wildcard_matching(temp_registry_file):
    service = CapabilityRegistryService(temp_registry_file)
    
    # Domain wildcard
    matches = service.matches_wildcard("workday.hcm.*")
    assert matches == {"workday.hcm.get_employee"}
    
    # Global wildcard
    matches = service.matches_wildcard("*")
    assert len(matches) == 3
    
    # No matches
    matches = service.matches_wildcard("invalid.*")
    assert matches == set()

def test_validate_capability_list(temp_registry_file):
    service = CapabilityRegistryService(temp_registry_file)
    
    # Valid list
    errors = service.validate_capability_list(["workday.hcm.get_employee", "workday.time.*"])
    assert not errors
    
    # Invalid exact match (typo)
    errors = service.validate_capability_list(["workday.hcm.get_employe"])
    assert len(errors) > 0
    assert "Unknown capability: 'workday.hcm.get_employe'" in errors[0]
    assert "workday.hcm.get_employee" in errors[1] # Suggestion

    # Invalid wildcard
    errors = service.validate_capability_list(["invalid.*"])
    assert len(errors) == 1
    assert "matches no capabilities" in errors[0]

def test_get_mfa_required(temp_registry_file):
    service = CapabilityRegistryService(temp_registry_file)
    mfa_caps = service.get_mfa_required()
    assert len(mfa_caps) == 1
    assert mfa_caps[0].id == "workday.payroll.get_pay_statement"

def test_duplicate_id_check():
    data = {
        "version": "1.0",
        "metadata": {"last_updated": "x", "owner": "x", "description": "x"},
        "capabilities": [
            {"id": "dup", "name": "n1", "domain": "d", "type": "action", "sensitivity": "low"},
            {"id": "dup", "name": "n2", "domain": "d", "type": "action", "sensitivity": "low"}
        ]
    }
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(data, f)
        temp_path = f.name
    
    with pytest.raises(ValueError, match="Duplicate capability IDs"):
        CapabilityRegistryService(temp_path)
    
    Path(temp_path).unlink()
