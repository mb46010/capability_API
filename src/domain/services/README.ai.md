# Policy Verification Framework README.ai.md

## Module Overview
The Policy Verification Framework is a declarative testing system designed to verify that security policies enforce intended access patterns. It simulates principals and requests to validate 'ALLOW'/'DENY' results, matched policies, and audit levels against the system's Policy Engine.

## Core Entities
- `PolicyTestSuite`: A YAML-defined collection of test cases with metadata and optional defaults.
- `PolicyTestCase`: A single interaction simulation (Principal + Request + Expected Outcome).
- `VerificationReport`: Aggregate metrics and detailed results from a verification run.

## Key Services
- `PolicyVerificationService`: Loads scenarios and executes them against the `PolicyEngine`.
- `PolicyReportGenerator`: Generates stakeholder-friendly HTML reports using Jinja2.

## CLI Usage
```bash
./scripts/verify-policy run --policy <path> --scenarios <dir> --format <table|json|junit|html>
```

## Reporting
- **HTML**: Stakeholder-friendly reports with summary metrics and security requirement mapping.
- **JUnit XML**: Integration with CI/CD test dashboards.
- **JSON**: Machine-readable data for custom automation.

## CI/CD Integration
- **GitHub Actions**: `.github/workflows/policy-verification.yml` runs on PRs touching policies or scenarios.
- **Pre-commit**: `scripts/pre-commit-verify` can be linked to `.git/hooks/pre-commit` for local safety.

## Directory Structure
- `src/domain/entities/policy_test.py`: Pydantic models for declarative scenarios.
- `src/domain/services/policy_verifier.py`: Core logic for executing tests.
- `src/domain/services/policy_report_generator.py`: HTML report generation.
- `tests/policy/scenarios/`: Directory for YAML test scenarios.
  - `baseline.yaml`: Core access patterns for Admins, Employees, and AI Agents.
  - `regression.yaml`: Wildcard expansion and regression safety tests.

## Development Standards
- **TDD**: Write failing test scenarios before updating policies or framework logic.
- **Article VIII**: Mask all PII in logs. Use synthetic IDs in scenarios.
- **Hexagonal**: Verification logic must remain storage-agnostic, using the filesystem port for scenario loading.
