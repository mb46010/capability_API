# Tasks: HR Platform MCP Server

**Branch**: `005-hr-mcp-server`
**Input**: Design documents from `/specs/005-hr-mcp-server/`

## Phase 1: Setup

**Goal**: Initialize project structure and dependencies.

- [X] T001 Create MCP project structure in `src/mcp/`, `src/mcp/tools/`, `src/mcp/adapters/`, `src/mcp/models/`, `src/mcp/lib/`
- [X] T002 Update `requirements.txt` with `fastmcp>=3.0.0b1`, `pydantic-settings`, `PyJWT`, and `httpx`
- [X] T003 Implement configuration management using `pydantic-settings` in `src/mcp/lib/config.py`
- [X] T004 Create `src/mcp/__init__.py` and `src/mcp/tools/__init__.py`

## Phase 2: Foundational

**Goal**: Implement core utilities and shared adapters.

- [X] T005 [P] Implement PII-masking logging filter in `src/mcp/lib/logging.py` (Constitution Article VIII)
- [X] T006 [P] Implement Backend client for Capability API communication in `src/mcp/adapters/backend.py`
- [X] T007 [P] Implement Auth Context extractor for OIDC token inspection in `src/mcp/adapters/auth.py`
- [X] T008 [P] Implement semantic error mapper in `src/mcp/lib/errors.py`
- [X] T009 Initialize FastMCP server instance in `src/mcp/server.py`

## Phase 3: US1 - AI Agent Limited Access (P1)

**Goal**: Enable restricted organizational lookup for AI Agents.

**Independent Test**: Execute `get_employee` as an AI Agent and verify PII fields are omitted.

- [X] T010 [P] [US1] Define Employee and Org Chart Pydantic models in `src/mcp/models/hcm.py`
- [X] T011 [US1] Create unit tests for HCM tool authorization and filtering in `tests/unit/mcp/test_hcm_tools.py`
- [X] T012 [US1] Implement `get_employee` tool with backend-filtered response passthrough in `src/mcp/tools/hcm.py`
- [X] T013 [US1] Implement `get_manager_chain` and `get_org_chart` tools in `src/mcp/tools/hcm.py`
- [X] T014 [US1] Implement `update_contact_info` tool in `src/mcp/tools/hcm.py`
- [X] T015 [US1] Register HCM tools in `src/mcp/server.py`
- [X] T016 [US1] Integration test for AI Agent data filtering in `tests/integration/mcp/test_ai_agent_scenarios.py`

## Phase 4: US2 - Self-Service Time Management (P1)

**Goal**: Allow employees to manage their own time-off requests.

**Independent Test**: Execute `request_time_off` as an employee and verify it appears in the backend.

- [X] T017 [P] [US2] Define TimeOffRequest and Balance Pydantic models in `src/mcp/models/time.py`
- [X] T018 [US2] Create unit tests for Time tools in `tests/unit/mcp/test_time_tools.py`
- [X] T019 [US2] Implement `get_pto_balance` tool in `src/mcp/tools/time.py`
- [X] T020 [US2] Implement `request_time_off` with auto-generated Transaction ID in `src/mcp/tools/time.py`
- [X] T021 [US2] Implement `cancel_time_off` tool in `src/mcp/tools/time.py`
- [X] T022 [US2] Register Time tools in `src/mcp/server.py`
- [X] T023 [US2] Integration test for employee time-off flow in `tests/integration/mcp/test_employee_flows.py`

## Phase 5: US3 - Manager Approval Lifecycle (P1)

**Goal**: Enable managers to oversee and approve requests.

**Independent Test**: Execute `approve_time_off` as a manager for a subordinate's request and verify success.

- [X] T024 [US3] Create unit tests for manager-specific tools in `tests/unit/mcp/test_manager_tools.py`
- [X] T025 [US3] Implement `list_direct_reports` tool in `src/mcp/tools/hcm.py`
- [X] T026 [US3] Implement `approve_time_off` tool in `src/mcp/tools/time.py`
- [X] T027 [US3] Register manager-only tools in `src/mcp/server.py`
- [X] T028 [US3] Integration test for manager approval lifecycle in `tests/integration/mcp/test_manager_scenarios.py`

## Phase 6: US4 - MFA-Protected Payroll Access (P2)

**Goal**: Secure sensitive payroll data with MFA enforcement.

**Independent Test**: Execute `get_compensation` without MFA and verify `MFA_REQUIRED` 401 error.

- [X] T029 [P] [US4] Define Compensation and Pay Statement Pydantic models in `src/mcp/models/payroll.py`
- [X] T030 [US4] Create unit tests for Payroll tools and MFA checks in `tests/unit/mcp/test_payroll_tools.py`
- [X] T031 [US4] Implement `get_compensation` tool with MFA enforcement in `src/mcp/tools/payroll.py`
- [X] T032 [US4] Implement `get_pay_statement` tool in `src/mcp/tools/payroll.py`
- [X] T033 [US4] Register Payroll tools in `src/mcp/server.py`
- [X] T034 [US4] Integration test for MFA-protected access in `tests/integration/mcp/test_security_scenarios.py`

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Finalize security, performance, and documentation.

- [X] T035 Implement dynamic tool discovery logic (filtering `list_tools`) in `src/mcp/server.py`
- [X] T036 Implement latency benchmarking tests in `tests/performance/mcp/test_latency.py`
- [X] T037 Update `docs/architecture.md` with MCP server integration details
- [X] T038 Conduct final end-to-end smoke test across all personas

## Dependencies & Execution Order

1. **Phase 1 & 2** are strict prerequisites for any tool implementation.
2. **US1 (Phase 3)** and **US2 (Phase 4)** are independent and can be started in parallel after Phase 2.
3. **US3 (Phase 5)** depends on US1 (for reports) and US2 (for requests).
4. **US4 (Phase 6)** is independent and can be started after Phase 2.
5. **Phase 7** requires all tool phases to be complete.

## Parallel Execution Examples

- **Developer A**: T010, T012, T013 (US1 Implementation)
- **Developer B**: T017, T019, T020 (US2 Implementation)
- **Developer C**: T029, T031, T032 (US4 Implementation)

## Implementation Strategy

- **MVP Scope**: Complete Phase 1, 2, and 3 (US1). This provides the first functional governed interface for AI Agents.
- **Incremental Delivery**: Following the MVP, deliver US2 (Self-service), then US3 (Manager workflow), and finally US4 (Sensitive data).