# Feature Specification: Capability Registry

**Feature Branch**: `007-capability-registry`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description (PRD Option C)

## Clarifications

### Session 2026-01-31
- Q: For this Phase 1 implementation, how should the registry store capability definitions? → A: Single File (Monolithic): All capabilities defined in `config/capabilities/index.yaml`.
- Q: How should the system handle runtime requests for capabilities marked as `deprecated: true`? → A: Allow with Warning Log: Execute the request but emit a warning log.

## Feature Classification *(mandatory)*

- **Type**: ACTION
- **Rationale**: The capability registry provides synchronous validation and lookup services. It acts as a foundational infrastructure component used by other actions and flows.
- **Idempotency Strategy**: The registry is read-only at runtime. Loading or reloading the registry from disk is idempotent and side-effect free.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Startup Policy Validation (Priority: P1)

As a System Administrator, I want the server to fail at startup if any policy references a non-existent capability, so that I don't discover configuration errors only when users get runtime errors.

**Why this priority**: Prevents "silent failures" where bad configuration looks valid but fails in production. Addresses the critical "Policy Validation Gap".

**Independent Test**: Create a policy file with a typo in a capability name, try to start the server/loader, and verify it fails with a specific error message suggesting the correct name.

**Acceptance Scenarios**:

1. **Given** a policy file referencing "workday.hcm.get_employe" (typo), **When** the server starts, **Then** the process terminates with an error "Unknown capability: 'workday.hcm.get_employe'. Did you mean: workday.hcm.get_employee".
2. **Given** a valid policy file, **When** the server starts, **Then** the process continues successfully.
3. **Given** a policy using a wildcard "workday.hcm.*", **When** the server starts, **Then** it validates that matching capabilities exist.

---

### User Story 2 - Runtime Request Validation (Priority: P2)

As a Developer or Service User, I want the system to validate requested actions against the registry at runtime, so that invalid requests are rejected as "Bad Request" (400) rather than "Access Denied" (403).

**Why this priority**: Improves debugging and API experience. Ensures the "Single Source of Truth" is enforced at runtime.

**Independent Test**: Send an API request for a non-existent action and verify a 400 response with suggestions.

**Acceptance Scenarios**:

1. **Given** a running server, **When** I request "workday.hcm.nonexistent", **Then** I receive a 400 Bad Request with a message "Unknown capability".
2. **Given** a running server, **When** I request "workday.hcm.get_employee", **Then** the request proceeds to the adapter.
3. **Given** a running server, **When** I request a capability marked `deprecated: true`, **Then** the request succeeds but a warning is logged.

---

### User Story 3 - CLI Registry Management (Priority: P3)

As a Platform Engineer, I want command-line tools to list available capabilities and validate registry structure, so that I can easily inspect what is available and ensure my changes are correct.

**Why this priority**: Enables "Capability Discovery" and simplifies maintenance.

**Independent Test**: Run the CLI tool to list capabilities and verify output matches the YAML file.

**Acceptance Scenarios**:

1. **Given** the registry file, **When** I run `scripts/capability-registry list`, **Then** I see a table of all capabilities.
2. **Given** a policy file, **When** I run `scripts/capability-registry check-policy my-policy.yaml`, **Then** it reports whether the policy is valid against the registry.

### Edge Cases

- **Missing Registry**: If `config/capabilities/index.yaml` is missing, the application MUST fail to start.
- **Duplicate IDs**: If the registry contains duplicate Capability IDs, the loader MUST raise an error.
- **Wildcards**: If a policy uses a wildcard that matches NO capabilities (e.g. `service.unknown.*`), validation MUST fail.
- **Deprecated Usage**: Invoking a deprecated capability MUST generate a warning log but allow execution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST load all capability definitions from a single monolithic YAML file at `config/capabilities/index.yaml`.
- **FR-002**: System MUST enforce unique `id` for each capability and validate metadata (domain, type, sensitivity, tags, MFA requirement).
- **FR-003**: System MUST provide a Singleton `CapabilityRegistryService` that loads the registry once at startup.
- **FR-004**: The Registry Service MUST support exact match lookups and wildcard pattern matching (e.g., `domain.subdomain.*`).
- **FR-005**: The Registry Service MUST provide "fuzzy search" suggestions for invalid capability IDs (typo detection).
- **FR-006**: The Policy Loader MUST validate all capability references in policy files against the registry at startup.
- **FR-007**: The ActionService MUST use the registry to validate incoming requests, returning 400 for unknown capabilities.
- **FR-008**: System MUST provide a CLI tool (`scripts/capability-registry`) to list, validate, and query the registry.
- **FR-009**: The CLI tool MUST support checking a specific policy file against the registry.
- **FR-010**: System MUST include a CI/CD script/workflow to validate the registry and policies on pull requests.
- **FR-011**: The ActionService MUST log a warning message when a request targets a capability marked as `deprecated: true`.

### Key Entities

- **Capability**: A discrete unit of functionality (Action or Flow). Attributes: `id`, `name`, `domain`, `type`, `sensitivity`, `requires_mfa`, `tags`, `deprecated`.
- **CapabilityRegistry**: The authoritative collection of all Capabilities, loaded from YAML.
- **Policy**: An access control rule set that references Capabilities (subject to validation).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of policy files referencing non-existent capabilities cause a startup failure (Typo Detection).
- **SC-002**: Registry loading and validation adds less than 50ms to the application startup time.
- **SC-003**: Runtime capability lookups have 0ms perceptible overhead (using in-memory O(1) lookups).
- **SC-004**: Developers can add a new capability and validate it using the CLI in under 1 minute.
- **SC-005**: All existing 13 capabilities (11 actions, 2 flows) are correctly defined in the initial registry.