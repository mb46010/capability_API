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

## 3. Getting Started

### Prerequisites
- **Node.js**: Version 18 or 20.
- **Yarn**: Classic (`1.x`).
- **Docker**: Required for running TechDocs locally and some plugins.

### Installation
If you don't have a Backstage instance, you can create a new one:
```bash
npx @backstage/create-app@latest
```
Follow the prompts to name your app and select the database (SQLite is easiest for local testing).

### Configuring this Repository
To see the Capability API governance data in your Backstage instance, you need to register the root `catalog-info.yaml` file.

1.  **Generate the Catalog**:
    ```bash
    python3 scripts/generate_catalog.py
    ./scripts/verify-policy run
    ```

2.  **Register in Backstage (Local Development)**:
    Since the Backstage UI often blocks `file://` paths for security, the recommended way to register local files is by adding them to your `app-config.yaml`:

    ```yaml
    # In your Backstage project's app-config.yaml
    catalog:
      locations:
        - type: file
          target: /absolute/path/to/capability_API/catalog-info.yaml
    ```

3.  **Register in Backstage (Production)**:
    Once your code is pushed to a Git provider (GitHub, GitLab, etc.), you can use the URL to the file in the UI:
    - Open Backstage (e.g., `http://localhost:3000`).
    - Click **Register Existing Component**.
    - Enter the URL: `https://github.com/your-org/capability_API/blob/main/catalog-info.yaml`

### TechDocs Setup
To build the documentation (including patches for C4 diagrams), use the provided script:
```bash
./scripts/make_docs.sh
```

To view the verification reports locally, ensure you have the `mkdocs` and `mkdocs-techdocs-core` plugin installed, or use the Backstage CLI to preview:
```bash
npx @backstage/cli techdocs-cli preview --storage-name local
```

---

## 4. Continuous Sync (CI/CD)
Governance visibility is enforced through our GitHub Actions workflows:
- **Sync Check**: PRs are blocked if the catalog entities in `catalog/` are out of sync with `config/capabilities/index.yaml`.
- **Automatic Publishing**: The verification report is regenerated and published to TechDocs on every merge to `main`.

---

## Developer Reference
- **Root Configuration**: `catalog-info.yaml` (Defines the Component, Systems, and Locations)
- **Generator Script**: `scripts/generate_catalog.py`
- **Verifier Script**: `scripts/verify-policy`
- **Templates**: `scripts/templates/`
- **TechDocs Home**: `docs/index.md`
- **TechDocs Output**: `docs/policy-verification/latest.md`
- **Configuration**: `mkdocs.yml`
