import pytest
import os
import sys
from unittest.mock import MagicMock, patch
from src.domain.entities.capability import CapabilityEntry, CapabilityType, SensitivityLevel

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from scripts import generate_catalog

def test_validate_mermaid_flow_valid():
    registry = MagicMock()
    cap = CapabilityEntry(
        id="test.cap",
        name="Test",
        domain="test",
        type=CapabilityType.FLOW,
        sensitivity=SensitivityLevel.LOW,
        implementation_flow="A -->|workday.hcm.get_employee| B",
        requires_capabilities=["workday.hcm.get_employee"]
    )
    errors = generate_catalog.validate_mermaid_flow(cap, registry)
    assert not errors

def test_validate_mermaid_flow_missing_required():
    registry = MagicMock()
    cap = CapabilityEntry(
        id="test.cap",
        name="Test",
        domain="test",
        type=CapabilityType.FLOW,
        sensitivity=SensitivityLevel.LOW,
        implementation_flow="A -->|workday.hcm.get_employee| B",
        requires_capabilities=[]
    )
    errors = generate_catalog.validate_mermaid_flow(cap, registry)
    assert len(errors) == 1
    assert "referenced in Mermaid flow but missing from requires_capabilities" in errors[0]

def test_validate_mermaid_flow_extra_required():
    registry = MagicMock()
    cap = CapabilityEntry(
        id="test.cap",
        name="Test",
        domain="test",
        type=CapabilityType.FLOW,
        sensitivity=SensitivityLevel.LOW,
        implementation_flow="A --> B",
        requires_capabilities=["workday.hcm.get_employee"]
    )
    errors = generate_catalog.validate_mermaid_flow(cap, registry)
    assert len(errors) == 1
    assert "in requires_capabilities but not referenced in Mermaid flow labels" in errors[0]
