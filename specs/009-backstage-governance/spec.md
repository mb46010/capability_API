# Feature Specification: Backstage.io Governance Integration

**Feature Branch**: `009-backstage-governance`  
**Created**: 2026-02-02  
**Status**: Draft  
**Input**: User description: (See PRD in context)

## Feature Classification *(mandatory)*

- **Type**: FLOW
- **Rationale**: This feature integrates multiple distinct systems (Capability API, CI/CD, Backstage) and involves multi-step processes like catalog generation, report publishing, and runtime data proxying. It creates a "governance lens" flow rather than a single atomic action.
- **Idempotency Strategy**: The catalog generator script (`scripts/generate_catalog.py`) will be strictly idempotent (running it multiple times produces identical output). The policy verification report is a snapshot that is safely replaced on each run.

## Clarifications

### Session 2026-02-02
- Q: How should the Policy Verification HTML report be integrated into TechDocs? → A: Native Markdown (Update generator to output a .md file compatible with MkDocs).
- Q: How should the generated `catalog-info.yaml` files be organized on disk? → A: Grouped by Domain (Organize into subdirectories by domain, e.g., `catalog/workday-hcm/`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Capability Catalog (Priority: P1)

As a Risk Officer or Engineer, I want to browse a central inventory of all platform capabilities so that I can understand their sensitivity, MFA requirements, and domain grouping without reading source code.

**Why this priority**: This is the foundational layer. The catalog entities are required for the other two initiatives to link back to. Without this, the governance data is unstructured.

**Independent Test**: Can be tested by running the generator script and verifying the `catalog-info.yaml` output against the `index.yaml` source, then inspecting the rendered entities in a local Backstage instance.

**Acceptance Scenarios**:

1. **Given** a valid `config/capabilities/index.yaml` with 13 capabilities, **When** I run `scripts/generate_catalog.py`, **Then** it produces valid `catalog-info.yaml` files for each capability with correct metadata (domain, sensitivity, MFA).
2. **Given** a composite capability with a Mermaid diagram, **When** I view it in Backstage, **Then** I see the visualized flow diagram rendered correctly.
3. **Given** a change to a capability in `index.yaml` without regenerating the catalog, **When** CI runs, **Then** the pipeline fails with a clear diff.

---

### User Story 2 - Verify Policy Compliance (Priority: P2)

As a Compliance Officer, I want to view a human-readable report of policy test results so that I can verify the platform's access controls are functioning correctly.

**Why this priority**: High compliance value with low integration cost (static HTML via TechDocs). It builds trust in the system's enforcement.

**Independent Test**: Can be tested by running the policy verification suite and checking that the generated HTML report is accessible via the Backstage TechDocs URL for the service.

**Acceptance Scenarios**:

1. **Given** a policy change is committed, **When** the CI pipeline finishes, **Then** a new HTML verification report is published to TechDocs.
2. **Given** a PR introduces a policy violation, **When** CI runs, **Then** the verification step fails and blocks the merge.
3. **Given** I am on a Capability entity page in Backstage, **When** I look for governance info, **Then** I see a link to the Verification Dashboard.

### Edge Cases

- What happens if `index.yaml` contains invalid Mermaid syntax? (Generator should fail validation)
- What happens if a capability referenced in a policy does not exist in the catalog? (Generator should flag this or policy validation should catch it)

## Requirements *(mandatory)*

### Functional Requirements

**Initiative 1: Capability Catalog**
- **FR-001**: System MUST provide a build-time script (`scripts/generate_catalog.py`) to transform `config/capabilities/index.yaml` into Backstage `catalog-info.yaml` files, organized into subdirectories grouped by domain (e.g., `catalog/workday-hcm/`).
- **FR-002**: System MUST group capabilities by domain (workday-hcm, workday-time, workday-payroll) in the Backstage catalog.
- **FR-003**: System MUST display visual badges for sensitivity (low/medium/high/critical) and MFA requirements on capability entities.
- **FR-004**: System MUST compute and display a "Governed By" section on each capability entity, listing the policies that reference it (including wildcard matches).
- **FR-005**: System MUST render Mermaid diagrams for composite capabilities that include an `implementation_flow`.
- **FR-006**: System MUST validate that all capabilities referenced in a Mermaid flow diagram exist in `requires_capabilities`.
- **FR-007**: System MUST fail CI if the generated catalog files are out of sync with `index.yaml`.
- **FR-008**: System MUST include a link to the Policy Verification Dashboard on each capability entity page.

**Initiative 2: Policy Verification Dashboard**
- **FR-009**: System MUST generate a Markdown (.md) verification report on every policy or scenario change via CI, compatible with MkDocs.
- **FR-010**: System MUST publish the Markdown verification report to Backstage TechDocs under a "Governance" section.
- **FR-011**: System MUST block PRs that cause policy verification tests to fail.

### Key Entities

- **Capability**: A defined operation (action/flow) with metadata (sensitivity, MFA, domain).
- **Policy Verification Report**: A static HTML artifact summarizing the results of policy test scenarios.
- **Backstage Entity**: The representation of a Capability or System in the Backstage catalog.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of capabilities in `index.yaml` are visible and correctly searchable in the Backstage catalog.
- **SC-002**: Policy verification report is accessible in Backstage within 1 hour of the last policy merge.
- **SC-003**: CI pipeline fails 100% of the time if catalog files are stale or policy tests fail.