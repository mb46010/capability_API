# Tasks: Workday Simulator

**Branch**: `002-workday-simulator` | **Spec**: `/specs/002-workday-simulator/spec.md`

## Dependencies

- **Phase 1 (Setup)**: Blocks Phase 2
- **Phase 2 (Foundation)**: Blocks Phase 3, 4, 5
- **Phase 3 (HCM)**: Independent (MVP Candidate)
- **Phase 4 (Time)**: Independent (depends on Foundation)
- **Phase 5 (Payroll)**: Independent (depends on Foundation)

## Phase 1: Setup

Goal: Initialize the adapter module and configuration structures.

- [X] T001 Create adapter directory structure in `src/adapters/workday/`
- [X] T002 Create fixtures directory in `src/adapters/workday/fixtures/`
- [X] T003 Implement simulation configuration class in `src/adapters/workday/config.py`
- [X] T004 Define error taxonomy and exceptions in `src/adapters/workday/exceptions.py`
- [X] T005 [P] Create initial empty `__init__.py` exposing the public interface

## Phase 2: Foundation (Models & Fixtures)

Goal: Load realistic data from YAML fixtures into validated Pydantic models.

**Mandatory Tests**:
- [X] `tests/unit/adapters/workday/test_loader.py`: Verify YAML parsing and model validation.
- [ ] `tests/unit/adapters/workday/test_models.py`: Verify Pydantic validation rules.

**Tasks**:
- [X] T006 Create test file for fixture loader in `tests/unit/adapters/workday/test_loader.py`
- [X] T007 Define shared enum types (EmployeeStatus, etc.) in `src/adapters/workday/domain/types.py`
- [X] T008 [P] Define HCM Pydantic models (Employee, Job, etc.) in `src/adapters/workday/domain/hcm_models.py`
- [X] T009 [P] Define Time Tracking models in `src/adapters/workday/domain/time_models.py`
- [X] T010 [P] Define Payroll models in `src/adapters/workday/domain/payroll_models.py`
- [X] T011 Create default YAML fixtures (employees, depts) in `src/adapters/workday/fixtures/employees.yaml`
- [X] T012 Create time tracking fixtures in `src/adapters/workday/fixtures/time_tracking.yaml`
- [X] T013 Create payroll fixtures in `src/adapters/workday/fixtures/payroll.yaml`
- [X] T014 Implement YAML loader and internal state container in `src/adapters/workday/loader.py`
- [X] T015 Implement base `WorkdaySimulator` class with `execute` signature in `src/adapters/workday/client.py`

## Phase 3: HCM Operations (MVP)

Goal: Implement Human Capital Management (HCM) read/write operations.

**Mandatory Tests**:
- [X] `tests/integration/adapters/workday/test_hcm.py`: Test employee lookups, org charts, and updates.

**Tasks**:
- [X] T016 [US1] Create integration test file for HCM in `tests/integration/adapters/workday/test_hcm.py`
- [X] T017 [US1] Implement `get_employee` logic in `src/adapters/workday/services/hcm.py`
- [X] T018 [US1] Implement `get_employee_full` (sensitive) logic in `src/adapters/workday/services/hcm.py`
- [X] T019 [US1] Implement `list_direct_reports` logic in `src/adapters/workday/services/hcm.py`
- [X] T020 [US1] Implement `get_org_chart` (recursive) logic in `src/adapters/workday/services/hcm.py`
- [X] T021 [US1] Implement `get_manager_chain` logic in `src/adapters/workday/services/hcm.py`
- [X] T022 [US1] Implement `update_employee` (write) logic in `src/adapters/workday/services/hcm.py`
- [X] T023 [US1] Implement `terminate_employee` (write) logic in `src/adapters/workday/services/hcm.py`
- [X] T024 [US1] Wire HCM operations into `WorkdaySimulator.execute` dispatch in `src/adapters/workday/client.py`

## Phase 4: Time Tracking Operations

Goal: Implement Time Off requests, balances, and approvals.

**Mandatory Tests**:
- [X] `tests/integration/adapters/workday/test_time.py`: Test request lifecycles (Request -> Approve -> Cancel).

**Tasks**:
- [X] T025 [US2] Create integration test file for Time Tracking in `tests/integration/adapters/workday/test_time.py`
- [X] T026 [US2] Implement `get_balance` logic in `src/adapters/workday/services/time.py`
- [X] T027 [US2] Implement `list_requests` logic in `src/adapters/workday/services/time.py`
- [X] T028 [US2] Implement `get_request` logic in `src/adapters/workday/services/time.py`
- [X] T029 [US2] Implement `request_time_off` (validation) logic in `src/adapters/workday/services/time.py`
- [X] T030 [US2] Implement `approve_time_off` (manager check) logic in `src/adapters/workday/services/time.py`
- [X] T031 [US2] Implement `cancel_time_off` logic in `src/adapters/workday/services/time.py`
- [X] T032 [US2] Wire Time operations into `WorkdaySimulator.execute` dispatch in `src/adapters/workday/client.py`

## Phase 5: Payroll Operations

Goal: Implement Payroll read operations (compensation and pay statements).

**Mandatory Tests**:
- [X] `tests/integration/adapters/workday/test_payroll.py`: Verify access control and data correctness.

**Tasks**:
- [X] T033 [US3] Create integration test file for Payroll in `tests/integration/adapters/workday/test_payroll.py`
- [X] T034 [US3] Implement `get_compensation` logic in `src/adapters/workday/services/payroll.py`
- [X] T035 [US3] Implement `get_pay_statement` logic in `src/adapters/workday/services/payroll.py`
- [X] T036 [US3] Implement `list_pay_statements` logic in `src/adapters/workday/services/payroll.py`
- [X] T037 [US3] Wire Payroll operations into `WorkdaySimulator.execute` dispatch in `src/adapters/workday/client.py`

## Phase 6: Polish & Integration

Goal: Finalize error handling, configuration loading, and latency simulation.

- [X] T038 Add latency simulation middleware in `src/adapters/workday/client.py`
- [X] T039 Implement failure injection logic (configurable rates) in `src/adapters/workday/client.py`
- [X] T040 Register `WorkdayConnectorPort` implementation in main dependency container `src/api/dependencies.py`
- [X] T041 Verify PII masking in logs (manual verification or log capture test)
