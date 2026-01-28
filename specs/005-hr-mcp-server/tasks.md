# Tasks: HR Platform MCP Server

**Input**: Design documents from `/specs/005-hr-mcp-server/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure: `src/`, `src/tools/`, `src/adapters/`, `src/lib/`, `tests/unit/`, `tests/integration/`
- [ ] T002 Initialize Python project with `mcp[fastmcp]`, `httpx`, `pydantic-settings` dependencies in `requirements.txt`
- [ ] T003 [P] Configure `.env` and environment variables in `src/config.py`
- [ ] T004 Create `README.ai.md` for the module (Constitution Article VI)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T005 [P] Implement PII-masking logger in `src/lib/logging.py` (Constitution Article VIII)
- [ ] T006 [P] Implement Capability API async client in `src/adapters/backend_client.py`
- [ ] T007 [P] Implement Auth Context extractor and bearer passthrough logic in `src/adapters/auth.py`
- [ ] T008 [P] Implement backend error mapper (401, 403, 400) to MCP errors in `src/lib/errors.py`
- [ ] T009 Initialize FastMCP server instance in `src/mcp_server.py`

**Checkpoint**: Foundation ready - user tool implementation can now begin

---

## Phase 3: User Story 1 - AI Agent Limited Access (Priority: P1) 🎯 MVP

**Goal**: Ensure AI Agents get filtered data and restricted access to HCM tools.

**Independent Test**: Call `get_employee` with an AI Agent token and verify PII redaction.

### Tests for User Story 1

- [ ] T010 [P] [US1] Unit test for `get_employee` filtering in `tests/unit/test_hcm_tools.py`
- [ ] T011 [P] [US1] Integration test for AI Agent access denial in `tests/integration/test_security_filters.py`

### Implementation for User Story 1

- [ ] T012 [P] [US1] Define HCM entity schemas (Employee) in `src/models/hcm.py`
- [ ] T013 [US1] Implement `get_employee` tool with dynamic filtering and metadata tags in `src/tools/hcm.py`
- [ ] T014 [US1] Implement `get_manager_chain` and `get_org_chart` tools with metadata tags in `src/tools/hcm.py`
- [ ] T015 [US1] Add HCM tools to the main MCP server in `src/mcp_server.py`

**Checkpoint**: US1 functional - AI Agents can lookup organizational data safely.

---

## Phase 4: User Story 2 - Employee Self-Service Time Management (Priority: P1)

**Goal**: Enable employees to check PTO balances and submit requests.

**Independent Test**: Call `request_time_off` as an employee and verify the request appears in the backend simulator.

### Tests for User Story 2

- [ ] T016 [P] [US2] Unit test for `get_pto_balance` and `request_time_off` in `tests/unit/test_time_tools.py`

### Implementation for User Story 2

- [ ] T017 [P] [US2] Define Time Management entity schemas (TimeOffRequest) in `src/models/time.py`
- [ ] T018 [US2] Implement `get_pto_balance` tool with metadata tags in `src/tools/time.py`
- [ ] T019 [US2] Implement `request_time_off` tool with validation and metadata tags in `src/tools/time.py`
- [ ] T020 [US2] Add Time tools to the main MCP server in `src/mcp_server.py`

**Checkpoint**: US2 functional - Employees can manage their own leave.

---

## Phase 5: User Story 3 - Manager Approval Lifecycle (Priority: P1)

**Goal**: Enable managers to view and approve subordinates' requests.

**Independent Test**: Call `approve_time_off` as a manager for a report's request and verify success.

### Tests for User Story 3

- [ ] T021 [P] [US3] Unit test for manager relationship validation in `tests/unit/test_manager_tools.py`

### Implementation for User Story 3

- [ ] T022 [US3] Implement `list_direct_reports` tool (HCM domain) in `src/tools/hcm.py`
- [ ] T023 [US3] Implement `approve_time_off` and `cancel_time_off` tools in `src/tools/time.py`
- [ ] T024 [US3] Add manager-specific tool registration in `src/mcp_server.py`

**Checkpoint**: US3 functional - HR approval lifecycle is complete.

---

## Phase 6: User Story 4 - MFA-Protected Payroll Access (Priority: P2)

**Goal**: Secure compensation and pay statement data with MFA enforcement.

**Independent Test**: Call `get_compensation` without MFA and verify `MFA_REQUIRED` 401 error.

### Tests for User Story 4

- [ ] T025 [P] [US4] Unit test for Payroll MFA enforcement in `tests/unit/test_payroll_tools.py`

### Implementation for User Story 4

- [ ] T026 [P] [US4] Define Payroll entity schemas (Compensation) in `src/models/payroll.py`
- [ ] T027 [US4] Implement `get_compensation` and `get_pay_statement` tools in `src/tools/payroll.py`
- [ ] T028 [US4] Add Payroll tools with `sensitive` tags to the main MCP server in `src/mcp_server.py`

**Checkpoint**: US4 functional - Sensitive data is now MFA-protected.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final quality checks and discovery features.

- [ ] T029 Implement dynamic tool discovery logic (filtering `list_tools`) in `src/mcp_server.py`
- [ ] T030 [P] Update `docs/architecture.md` with MCP server sequence diagrams
- [ ] T031 Perform final integration smoke test using `scripts/api/smoke-test.sh`
- [ ] T032 Validate all success criteria in `quickstart.md`
- [ ] T033 [P] Implement latency benchmarking test to verify SC-004 (<100ms) in `tests/performance/test_latency.py`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1.
- **User Stories (Phase 3-6)**: Depend on Phase 2.
- **Polish (Phase 7)**: Depends on all core features (Phase 3-6).

### Parallel Opportunities

- T005, T006, T007, T008 can be implemented in parallel.
- Once Foundation (Phase 2) is complete, US1 (Phase 3), US2 (Phase 4), and US4 (Phase 6) can be started in parallel as they touch different domain files.
- US3 depends on US2 (for requests to approve) and US1 (for employee listing).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2.
2. Complete Phase 3 (US1).
3. Validate AI Agent filtering.

### Incremental Delivery

1. Foundation -> Organzational Lookup (HCM) -> Leave Management (Time) -> Payroll (MFA).
2. Each phase is a logical increment delivering specific domain value.
