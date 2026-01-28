# Feature Specification: HR Platform MCP Server

**Feature Branch**: `005-hr-mcp-server`  
**Created**: 2026-01-28  
**Status**: Draft  
**Input**: User description: "Design an MCP server for HR platform (FastMCP 3.0)"

## Feature Classification *(mandatory)*

- **Type**: ACTION (Interface for HR capabilities)
- **Rationale**: The MCP server acts as a gateway to HR backend services, providing a suite of 11 deterministic tools for AI models. It handles role-based discovery and multi-factor authentication enforcement at the interface layer.
- **Idempotency Strategy**: Read-only tools (lookup, chain, balance) are idempotent by design. Write actions (requesting time off, updating info) will utilize transaction IDs and optimistic concurrency (transaction ID/version check) provided by the backend to ensure request deduplication and prevent race conditions.

## Clarifications

### Session 2026-01-28
- Q: Data Filtering Responsibility → A: Backend (Capability API) filters data; MCP server returns result as-is.
- Q: Concurrent Time-Off Requests → A: Optimistic concurrency (transaction ID/version check prevents duplicates).
- Q: Token Refresh Handling → A: Return 401/error; client (Chainlit) re-authenticates and retries.
- Q: Dynamic Tool Listing → A: Dynamic tool listing; MCP server only exposes tools permitted for the caller's role.
- Q: Audit Log Detail Level → A: Metadata only for standard reads; Full payloads for writes and sensitive payroll tools.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI Agent Limited Access (Priority: P1)

As an administrator, I want AI Agents to have restricted access to employee data so that sensitive PII and salary information are never exposed to automated assistants.

**Why this priority**: Fundamental security requirement for deploying AI in HR. Ensures data privacy by default.

**Independent Test**: Can be tested by calling `get_employee` and `get_compensation` using an AI Agent identity and verifying field filtering and access denial.

**Acceptance Scenarios**:

1. **Given** an AI Agent principal, **When** calling `get_employee`, **Then** the response includes professional info (title, department) but excludes PII (personal email, phone).
2. **Given** an AI Agent principal, **When** calling `get_compensation`, **Then** the system returns a `FORBIDDEN` error with a message stating AI agents cannot access compensation data.

---

### User Story 2 - Self-Service Time Management (Priority: P1)

As an employee, I want to manage my own time-off requests using natural language so that I can check balances and submit requests efficiently.

**Why this priority**: Core utility for the broad employee base. Reduces friction in standard HR workflows.

**Independent Test**: Can be tested by an employee calling `get_pto_balance` followed by `request_time_off` and verifying the resulting "PENDING" state.

**Acceptance Scenarios**:

1. **Given** Alice (Employee) is logged in, **When** she asks "How much vacation time do I have?", **Then** the system returns her available, used, and pending hours.
2. **Given** Alice has sufficient balance, **When** she requests 5 days off, **Then** the system submits the request, assigns it to her manager (Bob), and returns a confirmation with a Request ID.

---

### User Story 3 - Manager Approval Lifecycle (Priority: P1)

As a manager, I want to view and approve my direct reports' requests so that I can maintain team coverage.

**Why this priority**: Critical for workflow completion. Enables managers to perform their duties through the AI interface.

**Independent Test**: Can be tested by Bob (Manager) calling `list_direct_reports` to find Alice's request and then calling `approve_time_off`.

**Acceptance Scenarios**:

1. **Given** Bob is Alice's manager, **When** Bob asks "Show me pending time off requests", **Then** the system identifies Alice's pending request.
2. **Given** Alice has a pending request, **When** Bob calls `approve_time_off`, **Then** the system validates the relationship, updates the status to "APPROVED", and restores/deducts hours as appropriate.

---

### User Story 4 - MFA-Protected Payroll Access (Priority: P2)

As an employee, I want my salary and pay statements to be protected by Multi-Factor Authentication (MFA) so that my financial data remains secure even if my primary session is compromised.

**Why this priority**: Ensures high-assurance security for the most sensitive personal data.

**Independent Test**: Calling `get_compensation` without an MFA-verified token must return an `MFA_REQUIRED` error.

**Acceptance Scenarios**:

1. **Given** a user has a standard token (no MFA), **When** requesting compensation, **Then** the system returns a 401 `MFA_REQUIRED` error.
2. **Given** a user provides a token with an MFA claim, **When** requesting compensation, **Then** the system returns the base salary and bonus details.

### Edge Cases

- **Insufficient Balance**: Requesting 80 hours when only 40 are available must return a 400 `INSUFFICIENT_BALANCE` error with available vs requested details.
- **Invalid Approver**: An employee attempting to approve their own request or a request for someone who isn't a direct report must be blocked with an `INVALID_APPROVER` 403 error.
- **Session Expiry**: If a token expires, the system MUST return a 401 Unauthorized error, signaling the client to initiate re-authentication.
- **Role-Based Tool Visibility**: A non-admin user must not be able to "see" or call tools restricted to administrators or other roles they do not possess.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001 (HCM Tools)**: System MUST provide 5 tools: `get_employee`, `get_manager_chain`, `list_direct_reports` (manager-only), `get_org_chart`, and `update_contact_info`.
- **FR-002 (Time Tools)**: System MUST provide 4 tools: `get_pto_balance`, `request_time_off`, `cancel_time_off`, and `approve_time_off` (manager-only).
- **FR-003 (Payroll Tools)**: System MUST provide 2 tools: `get_compensation` (MFA required) and `get_pay_statement` (MFA required).
- **FR-004 (RBAC)**: System MUST enforce dynamic tool visibility during tool discovery: Admin (11 tools), Employee (8 tools), AI Agent (5 tools).
- **FR-005 (MFA)**: System MUST enforce `require_mfa: true` for all payroll domain tools.
- **FR-006 (Filtering)**: System MUST rely on the backend (Capability API) to dynamically filter tool output based on the principal's type (e.g., redact PII for AI Agents).
- **FR-007 (Relationships)**: System MUST validate manager-subordinate relationships for `list_direct_reports` and `approve_time_off`.
- **FR-008 (Auth)**: System MUST support bearer token passthrough from the client session to the backend Capability API.
- **FR-009 (Metadata)**: Tools MUST include metadata (tags, descriptions) for improved AI model selection (e.g., `hcm`, `sensitive`, `manager-only`).
- **FR-010 (Audit)**: System MUST log metadata (principal, timestamp, tool) for all interactions, and capture full request/response payloads ONLY for write actions and sensitive payroll domain tools (VERBOSE logging).

### Key Entities *(include if feature involves data)*

- **Employee Profile**: Professional (title, dept, manager) and Personal (email, phone, salary) data.
- **Time Off Request**: Entity containing Request ID, Status (Pending/Approved/Cancelled), dates, and hours.
- **Manager Chain**: A hierarchical list of employees representing the reporting line.
- **Auth Context**: The security principal (User ID, Role, MFA Status) derived from the bearer token.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of Payroll access attempts without an MFA claim result in an MFA_REQUIRED error.
- **SC-002**: AI Agents receive 0% of PII fields (personal email/phone) when calling employee lookup tools.
- **SC-003**: Users can complete a common leave request flow in under 3 minutes of interaction (measured via total timestamp delta between first and last tool call in a session audit log).
- **SC-004**: System latency for tool execution (excluding backend) is under 100ms.
- **SC-005**: 100% of tool interactions generate an audit log entry with PII correctly redacted where applicable.