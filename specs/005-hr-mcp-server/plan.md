# Implementation Plan: HR Platform MCP Server

**Feature Branch**: `005-hr-mcp-server`  
**Spec**: [spec.md](./spec.md)  
**Research**: [research.md](./research.md)

## Technical Context

| Area | Choice | Rationale |
|------|--------|-----------|
| **Language** | Python 3.11+ | Constitutional requirement (Article I) |
| **Framework** | FastMCP 3.0 | Modern, Python-native MCP implementation with high-level abstractions |
| **Communication** | HTTP/1.1 (JSON) | Standard interface for Capability API calls |
| **Auth** | Bearer Passthrough | Stateless adapter pattern; preserves backend policy enforcement |
| **Testing** | Pytest | Project standard; support for async testing |

## Constitution Check

| Article | Requirement | Compliance Strategy |
|---------|-------------|---------------------|
| **I** | Python-Native | Entire MCP server implemented in Python using FastMCP |
| **II** | Hexagonal Integrity | MCP server acts as a Protocol Adapter (Adapter layer) |
| **III** | Idempotency | Passthrough of transaction IDs to backend; optimistic concurrency |
| **IV** | TDD | Unit tests for tool routing and error mapping before implementation |
| **VIII** | PII Masking | All logs redacting sensitive fields; VERBOSE restricted to audit trail |

## Development Gates

- [x] **Spec Approved**: Feature specification finalized and clarified.
- [x] **Research Complete**: FastMCP 3.0 integration patterns validated.
- [ ] **Data Model Defined**: Entities and validation rules documented.
- [ ] **Contracts Finalized**: OpenAPI schema for backend interaction complete.
- [ ] **Test Coverage**: 80%+ unit test coverage for tool logic.

## Milestones

### Milestone 1: Core Connectivity & Auth
- Initialize FastMCP server.
- Implement Bearer token extraction and passthrough logic.
- Verify connectivity to Capability API via a simple "ping" or health tool.

### Milestone 2: Domain Implementation (HCM & Time)
- Implement `workday.hcm.*` tools with role-based filtering logic.
- Implement `workday.time.*` tools with concurrency and balance validation.
- Add metadata tags for model discovery.

### Milestone 3: Payroll & MFA
- Implement `workday.payroll.*` tools.
- Implement the 401 MFA_REQUIRED error mapping.
- Verify verbose audit logging for financial actions.

### Milestone 4: Discovery & Polish
- Implement dynamic tool listing based on token claims.
- Add PII masking to standard logs.
- Final integration testing with Chainlit UI.

## Artifacts Generated
- `research.md`: Technical decisions and best practices.
- `data-model.md`: Schema and entity definitions.
- `contracts/openapi.yaml`: Backend interface contract.
- `quickstart.md`: Developer onboarding guide.