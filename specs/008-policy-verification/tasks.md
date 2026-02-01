# Tasks: Policy Verification Framework

**Input**: Design documents from `/specs/008-policy-verification/`
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/cli.md

**Tests**: Tests are MANDATORY per Constitution Article IV. Every user story includes mandatory test tasks.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure per implementation plan
- [x] T002 Initialize project with Pydantic V2, PyYAML, Jinja2, Tabulate dependencies
- [x] T003 [P] Configure linting and formatting tools for verification logic
- [x] T004 Create README.ai.md for Policy Verification module (Constitution Article VI)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 Setup Storage Port and local filesystem adapter for test scenarios (Article II)
- [x] T006 [P] Implement Pydantic models for Policy Verification in `src/domain/entities/policy_test.py`
- [x] T007 Configure provenance logging with PII masking for verification runs in `src/lib/logging.py` (Article VIII)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Developer Local Policy Verification (Priority: P1) 🎯 MVP

**Goal**: Enable developers to run a single command against a modified policy file and see immediate feedback.

**Independent Test**: Run `./scripts/verify-policy run` against a known "broken" policy and verify it reports correct failures.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T008 [P] [US1] Unit test for scenario loading and validation in `tests/unit/domain/test_policy_verifier.py`
- [x] T010 [P] [US1] Integration test for full verification run (ALLOW/DENY/Wildcard) in `tests/integration/test_policy_verification_e2e.py`

### Implementation for User Story 1

- [x] T011 [US1] Implement `PolicyVerificationService` evaluation logic using `PolicyEngine` in `src/domain/services/policy_verifier.py`
- [x] T012 [US1] Create CLI tool `src/scripts/verify-policy` with `run` and `list-scenarios` commands
- [x] T013 [US1] Implement baseline test scenarios (Positive/Negative) in `tests/policy/scenarios/baseline.yaml`
- [x] T014 [US1] Implement regression test scenarios (Wildcard expansion) in `tests/policy/scenarios/regression.yaml`
- [x] T015 [US1] Add validation for 'defaults' block in scenario loader

### Documentation for User Story 1 (MANDATORY)

- [x] T016 [US1] Update module README.ai.md and human docs with local verification usage and baseline test scenarios

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Automated CI/CD Guardrail (Priority: P1)

**Goal**: Automatically verify every policy change in the PR pipeline.

**Independent Test**: Submit a PR with a policy violation and verify GitHub Action fails and comments correctly.

### Tests for User Story 2 (MANDATORY) ⚠️

- [x] T017 [P] [US2] Unit test for JUnit XML and JSON report generation in `tests/unit/domain/test_policy_verifier.py`

### Implementation for User Story 2

- [x] T018 [US2] Implement JUnit XML and JSON formatters in `PolicyVerificationService`
- [x] T019 [US2] Create GitHub Actions workflow in `.github/workflows/policy-verification.yml`
- [x] T020 [US2] Implement shell script wrapper for pre-commit hook integration in `scripts/pre-commit-verify`

### Documentation for User Story 2 (MANDATORY)

- [x] T021 [US2] Update module README.ai.md with CI/CD integration and pre-commit hook setup instructions

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Compliance Reporting for Auditors (Priority: P2)

**Goal**: Generate human-readable HTML reports showing mapping to security requirements.

**Independent Test**: Generate an HTML report and verify it contains summary metrics and security requirement mapping.

### Tests for User Story 3 (MANDATORY) ⚠️

- [x] T022 [P] [US3] Unit test for HTML report generation logic in `tests/unit/domain/test_policy_report_generator.py`

### Implementation for User Story 3

- [x] T023 [US3] Create Jinja2 HTML template for stakeholder reports in `src/domain/services/templates/policy_report.html`
- [x] T024 [US3] Implement `PolicyReportGenerator` service in `src/domain/services/policy_report_generator.py`
- [x] T025 [US3] Integrate HTML reporting into CLI tool using `--format html`

### Documentation for User Story 3 (MANDATORY)

- [x] T026 [US3] Update module README.ai.md and human docs with compliance reporting details

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T027 Verify all 107+ scenarios against current policies (AI Agents, Employees, Managers, Admins)
- [x] T028 Code cleanup and refactoring for Article VII compliance (Modular Sovereignty)
- [x] T029 Run `quickstart.md` validation to ensure developer onboarding works as documented

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 is the MVP and should be completed first
  - User Story 2 and 3 can proceed in parallel after Story 1 baseline is established
- **Polish (Final Phase)**: Depends on all user stories being complete

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel
- Models and Base Infrastructure [P] within stories can run in parallel
- Report formatters [US2] and HTML generator [US3] can be developed in parallel once Story 1 logic is stable

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (MVP)
4. **STOP and VALIDATE**: Verify local CLI `run` works as expected
5. Commit baseline scenarios

### Incremental Delivery

1. Foundation ready
2. Add Story 1 → Baseline verification capability
3. Add Story 2 → CI/CD and safety guardrails
4. Add Story 3 → Compliance reporting
5. Final Polish → Verify full 107+ scenario coverage
