# Quickstart: Adding Policy Verification Tests

## 1. Create a Scenario File
Create a new YAML file in `tests/policy/scenarios/`.

```yaml
version: "1.0"
metadata:
  name: "My New Capability Tests"
  owner: "hr-security"
  description: "Verifying the new 'hr.transfer' flow"
  security_requirement: "SEC-009"

defaults:
  principal:
    type: "HUMAN"
    groups: ["employees"]
  request:
    environment: "prod"

test_cases:
  - id: "TRS-001"
    name: "Manager can initiate transfer for direct report"
    category: "positive"
    principal:
      subject: "MGR-001"
      groups: ["managers"]
    request:
      capability: "hr.transfer"
      parameters:
        employee_id: "EMP-042"
    expected:
      allowed: true
      policy_matched: "manager-transfer-permission"
```

## 2. Run Local Verification
Execute the verification script to test your changes.

```bash
./scripts/verify-policy run --scenarios tests/policy/scenarios/my_new_tests.yaml
```

## 3. Review the Report
Check the console output or generate an HTML report for details.

```bash
./scripts/verify-policy run --format table
```

## 4. Integration
Once your tests pass locally, commit them. The CI/CD pipeline will automatically run them on your Pull Request.
