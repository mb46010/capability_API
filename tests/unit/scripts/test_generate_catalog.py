import pytest
from unittest.mock import MagicMock, patch
from src.domain.entities.capability import CapabilityEntry, CapabilityType, SensitivityLevel
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from scripts import generate_catalog

def test_get_governing_policies():
    cap_to_policies = {
        "workday.*": ["admin-full-access"],
        "workday.hcm.get_employee": ["hr-staff-read"],
        "hr.*": ["hr-flows"]
    }
    
    policies = generate_catalog.get_governing_policies("workday.hcm.get_employee", cap_to_policies)
    assert "admin-full-access" in policies
    assert "hr-staff-read" in policies
    assert len(policies) == 2

def test_get_governing_policies_wildcard():
    cap_to_policies = {
        "workday.*": ["admin-full-access"],
    }
    policies = generate_catalog.get_governing_policies("workday.time.get_balance", cap_to_policies)
    assert policies == ["admin-full-access"]