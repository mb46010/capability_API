# Feature Specification: Backstage.io Governance Integration

**Feature Branch**: `009-backstage-governance`  
**Created**: 2026-02-02  
**Status**: Draft  
**Input**: User description: (See PRD in context)

## Feature Classification *(mandatory)*

- **Type**: FLOW
- **Rationale**: This feature integrates multiple distinct systems (Capability API, CI/CD, Backstage) and involves multi-step processes like catalog generation, report publishing, and runtime data proxying. It creates a "governance lens" flow rather than a single atomic action.
- **Idempotency Strategy**: The catalog generator script (`scripts/generate-catalog.py`) will be strictly idempotent (running it multiple times produces identical output). The policy verification report is a snapshot that is safely replaced on each run.

## Clarifications

### Session 2026-02-02
- Q: How should the Policy Verification HTML report be integrated into TechDocs? → A: Native Markdown (Update generator to output a .md file compatible with MkDocs).
- Q: How should the Audit Log Viewer plugin authenticate with the Capability API? → A: Backstage Proxy Auth (Backstage Backend handles auth and injects credentials).
- Q: Should the audit log proxy be implemented via a custom Backstage backend plugin or just configuration? → A: New Backend Plugin (Create a `capability-api-backend` plugin for proxy and future logic).
- Q: How should the generated `catalog-info.yaml` files be organized on disk? → A: Grouped by Domain (Organize into subdirectories by domain, e.g., `catalog/workday-hcm/`).
- Q: Who should have permission to export audit logs to CSV? → A: Admin Only (Only users in the `hr-platform-admins` group can export CSVs).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse Capability Catalog (Priority: P1)

As a Risk Officer or Engineer, I want to browse a central inventory of all platform capabilities so that I can understand their sensitivity, MFA requirements, and domain grouping without reading source code.

**Why this priority**: This is the foundational layer. The catalog entities are required for the other two initiatives to link back to. Without this, the governance data is unstructured.

**Independent Test**: Can be tested by running the generator script and verifying the `catalog-info.yaml` output against the `index.yaml` source, then inspecting the rendered entities in a local Backstage instance.

**Acceptance Scenarios**:

1. **Given** a valid `config/capabilities/index.yaml` with 13 capabilities, **When** I run `scripts/generate-catalog.py`, **Then** it produces valid `catalog-info.yaml` files for each capability with correct metadata (domain, sensitivity, MFA).
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

---

### User Story 3 - Inspect Audit Logs (Priority: P3)

As an Incident Responder, I want to search and filter audit logs in a UI so that I can investigate access events without parsing raw JSON logs.

**Why this priority**: High effort (custom plugin), but critical for operational security and investigations. Depends on the Catalog for dropdown data.

**Independent Test**: Can be tested by generating traffic to the API and verifying the events appear in the Backstage Audit Viewer plugin with correct filtering.

**Acceptance Scenarios**:

1. **Given** a set of recent API activities, **When** I open the Audit Log Viewer, **Then** I see a table of events including Timestamp, Actor, and Result.
2. **Given** I suspect a specific user is compromising the system, **When** I filter by Actor, **Then** I see only actions performed by that principal.
3. **Given** a denied request exists, **When** I view the logs, **Then** the row is visually highlighted (e.g., red background).

### Edge Cases

- What happens when the Backstage backend cannot reach the Capability API (network error)? (Plugin should show error/retry)
- What happens if `index.yaml` contains invalid Mermaid syntax? (Generator should fail validation)
- What happens if the audit log volume is very large? (Plugin should paginate)
- What happens if a capability referenced in a policy does not exist in the catalog? (Generator should flag this or policy validation should catch it)

## Requirements *(mandatory)*

### Functional Requirements

**Initiative 1: Capability Catalog**
- **FR-001**: System MUST provide a build-time script (`scripts/generate-catalog.py`) to transform `config/capabilities/index.yaml` into Backstage `catalog-info.yaml` files, organized into subdirectories grouped by domain (e.g., `catalog/workday-hcm/`).
- **FR-002**: System MUST group capabilities by domain (workday-hcm, workday-time, workday-payroll) in the Backstage catalog.
- **FR-003**: System MUST display visual badges for sensitivity (low/medium/high/critical) and MFA requirements on capability entities.
- **FR-004**: System MUST render Mermaid diagrams for composite capabilities that include an `implementation_flow`.
- **FR-005**: System MUST validate that all capabilities referenced in a Mermaid flow diagram exist in `requires_capabilities`.
- **FR-006**: System MUST fail CI if the generated catalog files are out of sync with `index.yaml`.

**Initiative 2: Policy Verification Dashboard**
- **FR-007**: System MUST generate a Markdown (.md) verification report on every policy or scenario change via CI, compatible with MkDocs.
- **FR-008**: System MUST publish the Markdown verification report to Backstage TechDocs under a "Governance" section.
- **FR-009**: System MUST block PRs that cause policy verification tests to fail.

**Initiative 3: Audit Log Viewer**
- **FR-010**: System MUST provide a custom `capability-api-backend` Backstage plugin to proxy requests to the Capability API's `/audit/recent` endpoint, handle authentication, and encapsulate backend integration logic.
- **FR-011**: System MUST provide a frontend plugin to display audit logs in a sortable, filterable table.
- **FR-012**: Users MUST be able to filter logs by Timestamp, Actor, Capability, Result, and MFA status.
- **FR-013**: System MUST visually highlight anomalous entries (denied requests, high auth age, sensitive access with short TTL).
- **FR-014**: Users MUST be able to view full details of an audit entry, including token provenance and redacted parameters, in a side drawer.
- **FR-015**: System MUST allow users in the `hr-platform-admins` group to export the filtered audit log view to CSV.

### Key Entities

- **Capability**: A defined operation (action/flow) with metadata (sensitivity, MFA, domain).
- **Policy Verification Report**: A static HTML artifact summarizing the results of policy test scenarios.
- **Audit Log Entry**: A structured record of an access attempt, including actor, token details, and outcome.
- **Backstage Entity**: The representation of a Capability or System in the Backstage catalog.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of capabilities in `index.yaml` are visible and correctly searchable in the Backstage catalog.
- **SC-002**: Policy verification report is accessible in Backstage within 1 hour of the last policy merge.
- **SC-003**: Audit log viewer renders and filters 10,000 log entries in under 2 seconds.
- **SC-004**: CI pipeline fails 100% of the time if catalog files are stale or policy tests fail.