# Policy Verification Module

## Overview
The Policy Verification module ensures that the Capability API's security posture remains intact across policy updates. it uses declarative YAML scenarios to simulate access requests and verify the Policy Engine's behavior.

## Key Features
- **Declarative Testing**: Security requirements defined as human-readable YAML.
- **CI/CD Integration**: Automatically blocks PRs that introduce over-permissive or broken policies.
- **Stakeholder Reporting**: Generates Markdown, HTML, and JUnit reports for compliance auditing.
- **Backstage TechDocs**: Automated publishing of the verification dashboard to Backstage.

## Important Links
- **[Technical README](../../src/domain/services/README.ai.md)**: Implementation details and CLI usage.
- **[Test Scenarios](../../tests/policy/scenarios/)**: Baseline and regression test definitions.
- **[Governance Dashboard](../backstage.md)**: Backstage integration details.

## Usage
To verify the current policy configuration and generate a Markdown report for TechDocs:
```bash
./scripts/verify-policy run --format table
```
The report is saved to `docs/policy-verification/latest.md`.
