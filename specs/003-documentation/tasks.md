# Tasks: Constitutional Documentation

**Branch**: `003-documentation` | **Spec**: `/specs/003-documentation/spec.md`

## Dependencies

- **Phase 1 (Setup)**: Blocks Phase 2
- **Phase 2 (Foundation)**: Blocks Phase 3, 4, 5
- **US3 (Contracts)**: High priority, improves US1 context.
- **US1 (Module READMEs)**: Depends on Phase 2.
- **US2 (Architecture)**: Depends on Phase 2.
- **US4/5 (Guides/Index)**: Depends on US1, US2, US3.

## Phase 1: Setup

Goal: Initialize the documentation directory structure.

- [X] T001 Create documentation root directory in `docs/`
- [X] T002 Create subdirectories for specific human guides in `docs/architecture/`, `docs/onboarding/`

## Phase 2: Foundational (Templates & Standards)

Goal: Define templates to ensure consistency across human and AI documentation.

- [X] T003 [P] Create AI-optimized README template in `docs/templates/README.ai.md`
- [X] T004 [P] Define Mermaid C4 container template in `docs/templates/architecture_template.md`

## Phase 3: US3 - Self-Documenting Contracts (P1)

Goal: Enhance all Pydantic models with descriptive metadata for OpenAPI quality.

**Mandatory Tests**:
- [X] `tests/unit/test_documentation_metadata.py`: Verify all model fields in domain/entities have descriptions.

**Tasks**:
- [X] T005 [P] [US3] Create metadata validation test in `tests/unit/test_documentation_metadata.py`
- [X] T006 [US3] Add descriptions to models in `src/domain/entities/action.py`
- [X] T007 [US3] Add descriptions to models in `src/domain/entities/flow.py`
- [X] T008 [US3] Add descriptions to models in `src/domain/entities/policy.py`
- [X] T009 [US3] Add descriptions to models in `src/domain/entities/error.py`
- [X] T010 [US3] Add descriptions to models in `src/adapters/workday/domain/hcm_models.py`
- [X] T011 [US3] Add descriptions to models in `src/adapters/workday/domain/time_models.py`
- [X] T012 [US3] Add descriptions to models in `src/adapters/workday/domain/payroll_models.py`

## Phase 4: US1 - AI Optimized READMEs (P1)

Goal: Provide high-density context for AI agents in every major code module.

**Tasks**:
- [X] T013 [US1] Create `README.ai.md` for Domain Services in `src/domain/services/README.ai.md`
- [X] T014 [US1] Create `README.ai.md` for Domain Ports in `src/domain/ports/README.ai.md`
- [X] T015 [US1] Create `README.ai.md` for Workday Adapter in `src/adapters/workday/README.ai.md`
- [X] T016 [US1] Create `README.ai.md` for Auth Adapter in `src/adapters/auth/README.ai.md`
- [X] T017 [US1] Create `README.ai.md` for Filesystem Adapters in `src/adapters/filesystem/README.ai.md`
- [X] T018 [US1] Create `README.ai.md` for API Routes in `src/api/routes/README.ai.md`
- [X] T019 [US1] Create `README.ai.md` for Common Utilities in `src/lib/README.ai.md`

## Phase 5: US2 - Architectural Guide (P1)

Goal: Create a central guide explaining the system design using C4 models.

**Tasks**:
- [X] T020 [US2] Implement System Context diagram (C4 Level 1) in `docs/architecture.md`
- [X] T021 [US2] Implement Container diagram (C4 Level 2) showing Hexagonal Ports in `docs/architecture.md`
- [X] T022 [US2] Document Port & Adapter mappings in `docs/architecture.md`

## Phase 6: Guides & Indexing (P2)

Goal: Finalize onboarding, troubleshooting, and global navigation.

**Tasks**:
- [X] T023 [US5] Create developer onboarding guide in `docs/onboarding.md`
- [X] T024 [US5] Create troubleshooting guide in `docs/troubleshooting.md`
- [X] T025 [US4] Update root `README.md` with a "Documentation Index" section linking all assets

## Final Phase: Polish

Goal: Verify all constitutional documentation requirements are met.

- [X] T026 Run `/speckit.analyze` to verify project-wide documentation consistency
- [X] T027 Manually verify generated FastAPI OpenAPI docs for field description inclusion

## Phase 8: Workday Adapter Tests

Goal: Add missing unit tests for the Workday Adapter.

**Tasks**:
- [X] T028 Create unit tests for Workday Simulator in `tests/unit/adapters/workday/test_client.py`

## Phase 9: Workday Service Tests



Goal: Add missing unit tests for the Workday Services (HCM, Time, Payroll).



**Tasks**:

- [X] T029 Create unit tests for HCM Service in `tests/unit/adapters/workday/services/test_hcm.py`

- [X] T030 Create unit tests for Time Service in `tests/unit/adapters/workday/services/test_time.py`

- [X] T031 Create unit tests for Payroll Service in `tests/unit/adapters/workday/services/test_payroll.py`




