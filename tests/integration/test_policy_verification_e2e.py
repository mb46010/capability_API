import pytest
from pathlib import Path
from src.domain.services.policy_verifier import PolicyVerificationService

def test_full_verification_run():
    # Use the actual policy file
    policy_path = "config/policy-workday.yaml"
    
    # Create a temporary scenario directory
    scenarios_dir = Path("tests/policy/scenarios_tmp")
    scenarios_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a baseline scenario
    baseline_content = """version: "1.0"
metadata:
  name: "Baseline Integration Tests"
  owner: "test"
  description: "Verify core policy matching"
  last_updated: "2026-02-01"
defaults:
  request:
    environment: "prod"
test_cases:
  - id: "INT-001"
    name: "Admin has full access"
    category: "positive"
    principal:
      type: "HUMAN"
      subject: "admin@local.test"
      groups: ["hr-platform-admins"]
      mfa_verified: true
    request:
      capability: "workday.hcm.get_employee"
    expected:
      allowed: true
      policy_matched: "admin-full-access"
      audit_level: "VERBOSE"
  
  - id: "INT-002"
    name: "AI Assistant can view PTO balances"
    category: "positive"
    principal:
      type: "AI_AGENT"
      subject: "agent-assistant@local.test"
      token_issued_at: 1000
      token_expires_at: 1100
    request:
      capability: "workday.time.get_balance"
    expected:
      allowed: true
      policy_matched: "ai-assistant-time-read"
  
  - id: "INT-003"
    name: "Unauthorized user is denied"
    category: "negative"
    principal:
      type: "HUMAN"
      subject: "unauthorized@local.test"
    request:
      capability: "workday.hcm.get_employee"
    expected:
      allowed: false
      reason_contains: "No matching policy"
"""
    (scenarios_dir / "baseline.yaml").write_text(baseline_content)
    
    verifier = PolicyVerificationService(policy_path)
    report = verifier.run_all_tests(str(scenarios_dir))
    
    # Cleanup
    (scenarios_dir / "baseline.yaml").unlink()
    scenarios_dir.rmdir()
    
    assert report.total_tests == 3
    assert report.passed == 3
    assert report.success is True

def test_wildcard_matching():
    policy_path = "config/policy-workday.yaml"
    verifier = PolicyVerificationService(policy_path)
    
    # Case that matches workday.*
    test = {
        "id": "WILD-001",
        "name": "Wildcard match test",
        "category": "positive",
        "principal": {
            "type": "HUMAN",
            "subject": "admin@local.test",
            "groups": ["hr-platform-admins"],
            "mfa_verified": True
        },
        "request": {
            "capability": "workday.anything.really",
            "environment": "prod"
        },
        "expected": {
            "allowed": True,
            "policy_matched": "admin-full-access"
        }
    }
    
    from src.domain.entities.policy_test import PolicyTestCase
    tc = PolicyTestCase(**test)
    result = verifier.run_test_case(tc)
    
    assert result.passed is True
    assert result.actual_policy == "admin-full-access"
