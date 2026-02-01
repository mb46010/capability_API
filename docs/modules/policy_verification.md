# Policy Verification Module

## Overview
The Policy Verification module ensures that the Capability API's security posture remains intact across policy updates. it uses declarative YAML scenarios to simulate access requests and verify the Policy Engine's behavior.

## Key Features
- **Declarative Testing**: Security requirements defined as human-readable YAML.
- **CI/CD Integration**: Automatically blocks PRs that introduce over-permissive or broken policies.
- **Stakeholder Reporting**: Generates HTML and JUnit reports for compliance auditing.

## Important Links
- **[Technical README](../../src/domain/services/README.ai.md)**: Implementation details and CLI usage.
- **[Test Scenarios](../../tests/policy/scenarios/)**: Baseline and regression test definitions.

## Usage
To verify the current policy configuration:
```bash
./scripts/verify-policy run --format table
```
