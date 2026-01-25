# Feature Specification: HR AI Platform Capability API

**Feature Branch**: `001-capability-api`
**Created**: 2026-01-25
**Status**: Draft

## Feature Classification *(mandatory)*

- **Type**: ACTION | FLOW
- **Rationale**: This is a comprehensive platform definition involving both short-lived deterministic operations (Actions) and long-running HR processes (Flows).
- **Idempotency Strategy**: Actions will use explicit schemas and audit semantics to ensure idempotency. Flows will use AWS Step Functions (simulated locally) with callback patterns and status tracking.

## Clarifications

### Session 2026-01-25
- Q: Which success metric is most critical for the initial Capability API release? → A: Functional success rate (95%+ of actions/flows succeed).
- Q: How should long-running flows handle transient failures in external connectors? → A: Fail-fast & notify (immediate halt + alert).
- Q: How should the system handle drift between the policy YAML and Okta? → A: Manual reconciliation (YAML flags drift; human fixes).
- Q: What is the preferred format for action response data? → A: JSON with Provenance (Nested object + metadata).
- Q: What is the primary method for onboarding new actions or flows? → A: Backstage Scaffolder (Template-driven creation).

## 1) Product framing and core principle
Build an HR AI Platform whose core product is a governed Capability API: a single, versioned OpenAPI surface exposing deterministic actions and flow triggers. Agents, workflows, admin tools, and user apps are interchangeable clients.

## Success Criteria
- **SC-001**: Functional success rate: 95%+ of triggered actions and flows must complete successfully or fail with a clear, auditable provenance log.

## 2) Actions vs flows
* Actions: short-lived, deterministic operations with explicit schemas, idempotency, and audit semantics (reads and writes).
* Flows: long-running HR processes (days or weeks) that sequence actions and wait for human input, without embedding business logic inside agents.

## 3) Identity, authorization, and configuration management (Okta OIDC)
Use Okta OIDC with distinct principal types:
* Humans (admins, operators)
* Machine workflows (system identity)
* AI agents (task-scoped, short TTL)

Authorization is capability-based: scopes map explicitly to actions and flows.
Maintain a curated policy YAML as a first-class platform artifact that:
* defines principals, scopes, allowed actions/flows, and environments
* references infrastructure tickets used to provision or modify Okta roles/clients
* records approval metadata (who/when/why)
* serves as the authoritative statement of intended access, independent of infra state

## 4) Orchestration model for HR delays
Model HR processes as long-running flows with explicit wait states for human approval. The flow runner is abstracted behind a start / status / cancel interface. Locally, use a mock runner; in cloud, this maps cleanly to AWS Step Functions (Standard) using callback patterns.

## 5) Connector and MCP strategy
Third-party MCP servers (e.g., Workday via CData) are treated strictly as connectors, not as trust or policy boundaries. Only approved, bounded operations are exposed via the Capability API so that scopes, audit, and determinism remain centralized and enforceable.

## 6) User experience strategy
For non-technical users, provide task-focused applications (forms, approvals, dashboards) backed by the same actions and flow triggers. Chat and conversational interfaces are optional, constrained clients rather than primary UX surfaces.

## 7) Admin and debugging model
Swagger/OpenAPI tooling is enabled as a controlled admin client for debugging, replay, and issue reproduction. Access is environment- and scope-gated. All executions are auditable and reproducible.

## 8) Local-first development and testing
Develop the full system locally from day one:
* Capability API with policy YAML enforcement
* Mock Okta/OIDC issuer or test realm
* Mock connectors (Workday, calendar, ticketing)
* Mock flow runner with realistic delays and callbacks
* Automated unit and integration tests

## 9) Future cloud deployment
The architecture is intentionally designed so local adapters can later be swapped for managed cloud services (e.g., Step Functions, managed connectors) without changing API contracts, policies, or authorization semantics.

## 10) Backstage from day one
Run Backstage locally from the start as the system-of-record for:
* Capability APIs, actions, and flows
* Ownership and responsibilities
* The curated policy YAML and generated “who-can-do-what” views
* Runbooks, tickets, and onboarding templates

## 11) Governance stance
Infrastructure provisions credentials. The curated YAML defines meaning. The API enforces reality.

## Functional Requirements
- **FR-001**: The system MUST return all action responses in a "JSON with Provenance" format. This structure includes a nested data object and a mandatory metadata object containing provenance information (e.g., source connector name, timestamp).
- **FR-002**: The platform MUST provide a Backstage Scaffolder template to standardize the onboarding of new actions and flows, ensuring all new capabilities include an OpenAPI definition, Python logic, and a `README.ai.md`.

## Edge Cases & Error Handling
- **Transient Connector Failures**: For long-running flows, any transient failure in an external connector (e.g., Workday) MUST trigger a "Fail-fast & notify" strategy. The flow execution is halted immediately, and an alert is generated for administrative intervention to prevent out-of-sync states.
- **Policy/Okta Drift**: The system MUST implement a "Manual reconciliation" strategy. If the curated policy YAML (the authoritative source) drifts from the actual state in Okta, the system flags the discrepancy via administrative alerts/Backstage views. A human operator is required to resolve the drift, ensuring no unauthorized access is accidentally granted.