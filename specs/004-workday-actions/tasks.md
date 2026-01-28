# Tasks: Workday Actions

**Input**: Design documents from `/specs/004-workday-actions/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create feature directory structure `src/adapters/workday/services` and `src/adapters/workday/fixtures`
- [ ] T002 Update `src/adapters/workday/README.ai.md` with new action capabilities and Pydantic schemas (Constitution Article VI)
- [ ] T003 Update `src/domain/entities/README.ai.md` with `ActionRequest`/`ActionResponse` documentation

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

- [ ] T004 [P] Implement `JSONLLogger` in `src/adapters/filesystem/logger.py` with PII redaction logic (Constitution Article VIII)
- [ ] T005 [P] Replace `print()` statements with `logging` in `src/adapters/workday/client.py` and integrate `JSONLLogger`
- [ ] T006 Define shared Pydantic models (`EmployeeReference`, `Money`, `ActionResponse`) in `src/domain/entities/action.py` (from `data-model.md`)
- [ ] T007 [P] Create `tests/conftest.py` fixture for `JSONLLogger` to verify redaction in tests

**Checkpoint**: Logging and base models ready - user stories can proceed

---

## Phase 3: User Story 1 - Read-Only Actions (Priority: P1)

**Goal**: Enable basic information retrieval for employees and agents

### Tests for User Story 1 (Constitution Article IV)
- [ ] T008 [P] [US1] Create unit tests for HCM service in `tests/unit/adapters/workday/services/test_hcm_actions.py` (fail first)
- [ ] T009 [P] [US1] Create unit tests for Time service in `tests/unit/adapters/workday/services/test_time_actions.py` (fail first)

### Implementation for User Story 1
- [ ] T010 [P] [US1] Implement `get_employee` logic in `src/adapters/workday/services/hcm.py` with field filtering for AI Agents
- [ ] T011 [P] [US1] Implement `get_balance` logic in `src/adapters/workday/services/time.py` with "Own Data" check
- [ ] T012 [P] [US1] Implement `get_manager_chain` logic in `src/adapters/workday/services/hcm.py`
- [ ] T013 [P] [US1] Implement `list_direct_reports` logic in `src/adapters/workday/services/hcm.py` with manager relationship check
- [ ] T014 [US1] Update `src/adapters/workday/client.py` to dispatch these new actions

**Checkpoint**: Read actions functional and testable

---

## Phase 4: User Story 2 - State-Mutating Actions (Priority: P2)

**Goal**: Enable employees to request time off and update their data

### Tests for User Story 2 (Constitution Article IV)
- [ ] T015 [P] [US2] Update `tests/unit/adapters/workday/services/test_time_actions.py` with state mutation tests (fail first)
- [ ] T016 [P] [US2] Update `tests/unit/adapters/workday/services/test_hcm_actions.py` with PII update tests (fail first)

### Implementation for User Story 2
- [ ] T017 [P] [US2] Implement `request` (time off) in `src/adapters/workday/services/time.py` (creates PENDING record)
- [ ] T018 [P] [US2] Implement `cancel` (time off) in `src/adapters/workday/services/time.py`
- [ ] T019 [P] [US2] Implement `update_contact_info` in `src/adapters/workday/services/hcm.py` with PII logging redaction
- [ ] T020 [US2] Update `src/adapters/workday/client.py` to dispatch mutation actions

**Checkpoint**: Mutation actions functional and auditable

---

## Phase 5: User Story 3 - Sensitive & Manager Actions (Priority: P3)

**Goal**: High-security actions (Compensation) and Manager approvals

### Tests for User Story 3 (Constitution Article IV)
- [ ] T021 [P] [US3] Create unit tests for Payroll service in `tests/unit/adapters/workday/services/test_payroll_actions.py` (fail first)
- [ ] T022 [P] [US3] Add approval security tests to `tests/unit/adapters/workday/services/test_time_actions.py`

### Implementation for User Story 3
- [ ] T023 [P] [US3] Implement `get_compensation` in `src/adapters/workday/services/payroll.py` with MFA check and verbose logging
- [ ] T024 [P] [US3] Implement `approve` in `src/adapters/workday/services/time.py` with manager relationship validation
- [ ] T025 [US3] Update `config/policy-workday.yaml` to enforce MFA for `get_compensation` and `update_contact_info`
- [ ] T026 [US3] Update `src/adapters/workday/client.py` dispatch logic

**Checkpoint**: All actions fully implemented and secured

---

## Phase 6: Polish & Integration

**Purpose**: Final verification and cleanup

- [ ] T027 [P] Run full integration test suite `tests/integration/test_scenarios.py` with new actions
- [ ] T028 Verify PII redaction in `logs/audit.jsonl` by running a sample `update_contact_info` request
- [ ] T029 Update `specs/004-workday-actions/quickstart.md` with verified curl commands