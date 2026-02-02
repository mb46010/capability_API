# Backstage.io Governance Integration

## Overview
The HR AI Platform integrates with [Backstage.io](https://backstage.io) to provide a "read-only governance lens" over the Capability API. This integration ensures that the platform's security posture, capability inventory, and compliance status are visible to non-technical stakeholders without changing the underlying enforcement model.

The integration consists of two main initiatives:
1. **Capability Catalog**: A browsable inventory of all Actions and Flows.
2. **Policy Verification Dashboard**: An interactive report of security test results.

---

## 1. Capability Catalog
The Capability Catalog transforms our internal `index.yaml` definitions into Backstage API entities. This allows stakeholders to browse capabilities by domain, check sensitivity levels, and see which policies govern each action.

### Key Features
- **Domain Grouping**: Capabilities are organized into Backstage Systems (e.g., `workday-hcm`, `workday-payroll`).
- **Sensitivity Badges**: Visual indicators for `low`, `medium`, `high`, and `critical` data sensitivity.
- **MFA Indicators**: Clearly marks capabilities that require Multi-Factor Authentication.
- **Policy Cross-Reference**: Each entity page includes a "Governed By" section listing the exact policies that grant access to it.
- **Implementation Flows**: Composite capabilities include visualized Mermaid diagrams showing their orchestration logic.

### Catalog Generation
The catalog is generated via a build-time script:
```bash
python3 scripts/generate_catalog.py
```
This script is executed in CI to ensure the Backstage view never diverges from the Git-committed configuration.

---

## 2. Policy Verification Dashboard
The Verification Dashboard provides a web-accessible view of the platform's access policy behavior. It is published as a Backstage TechDocs page.

### Features
- **Pass/Fail Metrics**: High-level summary of policy test scenarios.
- **Detailed Results**: A sortable table of all 107+ test cases, showing matched policies and execution times.
- **Staleness Detection**: The report includes a timestamp and is updated automatically on every policy change.

### Accessing the Dashboard
In Backstage, navigate to the **Capability API** component and select the **Docs** tab. The dashboard is located under the **Governance** section in the sidebar.

---

## 3. Continuous Sync (CI/CD)
Governance visibility is enforced through our GitHub Actions workflows:
- **Sync Check**: PRs are blocked if the catalog entities in `catalog/` are out of sync with `config/capabilities/index.yaml`.
- **Automatic Publishing**: The verification report is regenerated and published to TechDocs on every merge to `main`.

---

## Developer Reference
- **Generator Script**: `scripts/generate_catalog.py`
- **Templates**: `scripts/templates/`
- **TechDocs Output**: `docs/policy-verification/latest.md`
- **Configuration**: `mkdocs.yml`
