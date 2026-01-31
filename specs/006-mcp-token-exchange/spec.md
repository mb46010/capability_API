# Feature Specification: MCP Token Exchange

**Feature Branch**: `006-mcp-token-exchange`
**Created**: 2026-01-31
**Status**: Draft
**Input**: User description: "Implement OAuth 2.0 Token Exchange for MCP server to reduce blast radius and improve auditability."

## Feature Classification *(mandatory)*

- **Type**: ACTION
- **Rationale**: Token exchange is a discrete, short-lived, and deterministic cryptographic operation that transforms one token into another.
- **Idempotency Strategy**: Exchanging the same valid subject token with the same parameters will always yield a valid scoped token (though the `jti` may differ, the semantic result is identical).

## Clarifications

### Session 2026-01-31

- Q: Should the MCP Server cache exchanged tokens to reduce load? → A: Yes, Mandatory Caching. The MCP Server must cache exchanged tokens (e.g., with a 4-minute TTL) to minimize exchange requests.
- Q: Can an MCP token be exchanged for another MCP token (nesting)? → A: No, Reject Nesting. The exchange endpoint must reject requests where the `subject_token` is already an exchanged MCP token.
- Q: What if the original token lacks auth_time? → A: Default to iat. If auth_time is missing in the subject token, copy iat into the exchanged token's auth_time claim.

## User Scenarios & Testing *(mandatory)*

<!--
  IMPORTANT: User stories should be PRIORITIZED as user journeys ordered by importance.
  Each user story/journey must be INDEPENDENTLY TESTABLE - meaning if you implement just ONE of them,
  you should still have a viable MVP (Minimum Viable Product) that delivers value.
-->

### User Story 1 - Secure Token Exchange (Priority: P1)

As the MCP Server (acting on behalf of a user), I want to exchange the user's long-lived, broad-access token for a short-lived, restricted token before performing any actions, so that the risk of token theft is minimized.

**Why this priority**: This is the core security mechanism (Blast Radius Reduction) that this feature aims to deliver.

**Independent Test**: Can be tested by calling the Authentication Provider's exchange endpoint and verifying the resulting token's claims (TTL, scope) without needing the full MCP server or Policy Engine integration.

**Acceptance Scenarios**:

1. **Given** a valid user token with a 1-hour TTL, **When** the MCP server requests a token exchange with `scope=mcp:use`, **Then** the provider returns a new token with a 5-minute TTL and the `mcp:use` scope.
2. **Given** an exchanged MCP token, **When** inspected, **Then** it contains provenance claims (`acting_as: mcp-server`, `original_token_id`) linking it to the user's original token.

---

### User Story 2 - Scope-Based Access Enforcement (Priority: P1)

As a System Administrator, I want the Capability API to reject direct access attempts using MCP-scoped tokens, so that compromised MCP tokens cannot be used to bypass the MCP server's audit controls.

**Why this priority**: This enforces the "Privilege Scope" isolation, ensuring the exchanged token is useless outside its intended context.

**Independent Test**: Can be tested by manually obtaining an exchanged token and attempting to call an API endpoint directly (via curl/Postman).

**Acceptance Scenarios**:

1. **Given** a token with the `mcp:use` scope, **When** used to call the Capability API directly (without `acting_through` context or outside the MCP tool), **Then** the API rejects the request with a 403 Forbidden error.
2. **Given** a token with the `mcp:use` scope, **When** used by the MCP Server for a legitimate tool call, **Then** the API accepts the request.

---

### User Story 3 - Sensitive Action Freshness (Priority: P2)

As a Compliance Officer, I want sensitive operations (like accessing payroll data) to require recent authentication (e.g., within the last 5 minutes), so that an old or stolen session cannot be used for high-risk actions.

**Why this priority**: Enhances security for critical business functions ("Freshness Enforcement").

**Independent Test**: Can be tested by manipulating the `auth_time` claim in a test token and attempting to access a protected resource.

**Acceptance Scenarios**:

1. **Given** a valid user token where authentication occurred 10 minutes ago, **When** attempting to access a sensitive endpoint configured with `max_auth_age_seconds: 300`, **Then** the request is rejected with a 401 Unauthorized (MFA Required) error.
2. **Given** the user re-authenticates (updating `auth_time`), **When** attempting the same action, **Then** the request is allowed.

---

### User Story 4 - Provenance Audit (Priority: P2)

As a Security Auditor, I want to see the full chain of custody for every action in the logs, including whether it was performed directly or via the MCP server, so that I can accurately trace activity during a security incident.

**Why this priority**: Provides the "Auditability" benefit, crucial for distinguishing between human and agent actions.

**Independent Test**: Can be tested by running an action and inspecting the generated JSONL log entry for specific fields.

**Acceptance Scenarios**:

1. **Given** an action performed via the MCP Server, **When** reviewing the audit logs, **Then** the entry contains `acting_through: mcp-server`, `token_type: exchanged`, and `original_token_id`.
2. **Given** an action performed directly by a user, **When** reviewing the audit logs, **Then** the entry indicates direct access (no `acting_through` or `token_type: original`).

---

### Edge Cases

- **Token Expiry during Exchange**: What happens when the user token expires *during* the exchange process? The provider must reject the exchange.
- **Nested Exchange (Chain of Chains)**: The exchange endpoint MUST reject requests where the `subject_token` is already an exchanged token (identifiable by the `acting_as` claim).
- **Missing auth_time Claim**: If the subject token lacks an `auth_time` claim, the Authentication Provider MUST use the token's issue time (`iat`) as the `auth_time` in the exchanged token.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The Authentication Provider MUST support OAuth 2.0 Token Exchange (RFC 8693) to issue new tokens based on existing valid access tokens.
- **FR-002**: Exchanged tokens MUST have a significantly reduced Time-To-Live (TTL) (target: 5 minutes) compared to standard user tokens.
- **FR-003**: Exchanged tokens MUST contain a dedicated scope (e.g., `mcp:use`) and provenance claims (`acting_as`, `original_token_id`) while preserving the original user's identity (`sub`, `auth_time`).
- **FR-004**: The Policy Engine MUST support a `required_scope` condition to enforce that certain tokens can only be used for specific purposes.
- **FR-005**: The API Layer MUST reject requests using the dedicated MCP scope if they are not legitimate MCP tool invocations (Direct API Protection).
- **FR-006**: The Policy Engine MUST support a `max_auth_age_seconds` condition to enforce "Step-Up Authentication" for sensitive capabilities.
- **FR-007**: The Logging System MUST capture extended token metadata in audit logs, including `acting_through`, `token_scope`, `token_ttl_seconds`, and `auth_age_seconds`.
- **FR-008**: The MCP Server MUST automatically exchange the user's token for an MCP-scoped token before invoking any tools on the Capability API. It MUST cache valid exchanged tokens (e.g., for 4 minutes) to reuse them for subsequent calls within the same session, minimizing exchange overhead.

### Key Entities

- **User Token**: The initial long-lived (1hr) credential issued to the user upon login (e.g., by the Client Application).
- **MCP Token**: The short-lived (5min), scoped credential obtained by the MCP server via exchange.
- **Policy Rule**: Configuration entity defining access conditions, now extended with `required_scope` and `max_auth_age_seconds`.
- **Audit Entry**: A log record representing a system event, enriched with token provenance data.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Blast Radius Reduction: MCP-held tokens have a TTL of 5 minutes or less (a 92% reduction from the current 60 minutes).
- **SC-002**: Scope Isolation: 100% of direct API access attempts using an MCP-scoped token are rejected.
- **SC-003**: Audit Completeness: 100% of actions performed via the MCP server include the `acting_through` and `original_token_id` fields in the audit log.
- **SC-004**: Freshness Enforcement: Sensitive operations defined in policy reject any token with an `auth_age` greater than the configured limit (e.g., 300 seconds).