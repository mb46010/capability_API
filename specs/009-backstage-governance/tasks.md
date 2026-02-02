# Tasks: Backstage.io Governance Integration

**Input**: Design documents from `/specs/009-backstage-governance/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY per Constitution Article IV. The examples below include test tasks which must be generated for every user story.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Scripts**: `scripts/`
- **Config**: `config/`
- **Docs**: `docs/`
- **Tests**: `tests/`

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project structure for new scripts and docs per plan in `scripts/` and `docs/policy-verification/`
- [x] T002 [P] Create `specs/009-backstage-governance/contracts/catalog-entity.yaml` (if not exists) as reference contract
- [x] T003 Create `scripts/templates/catalog-info.yaml.j2` Jinja2 template for catalog entities
- [x] T004 Create `scripts/templates/verification-report.md.j2` Jinja2 template for policy report

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create shared Jinja2 environment setup utility in `src/lib/templating.py` (or similar shared lib)
- [x] T006 Ensure `CapabilityRegistryService` exposes necessary metadata (domain, sensitivity) for consumption by scripts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Browse Capability Catalog (Priority: P1) 🎯 MVP

**Goal**: Enable stakeholders to browse platform capabilities, sensitivity, and flows in Backstage.

**Independent Test**: Run `scripts/generate_catalog.py` and verify `catalog-info.yaml` files are created in `catalog/` with correct metadata and Mermaid diagrams.

### Tests for User Story 1 (MANDATORY) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [x] T007 [P] [US1] Create unit test for catalog generator logic in `tests/unit/scripts/test_generate_catalog.py` (mocking registry input)
- [x] T008 [P] [US1] Create integration test for idempotent generation in `tests/integration/scripts/test_catalog_generation.py`
- [x] T009 [P] [US1] Create test for Mermaid diagram validation logic in `tests/unit/scripts/test_mermaid_validation.py`

### Implementation for User Story 1

- [x] T010 [P] [US1] Implement `Capability` to Backstage Entity mapping logic in `scripts/generate_catalog.py`
- [x] T011 [P] [US1] Implement Mermaid diagram extraction and embedding logic in `scripts/generate_catalog.py`
- [x] T012 [P] [US1] Implement "Governed By" policy cross-reference computation in `scripts/generate_catalog.py`
- [x] T013 [US1] Implement main execution loop (file writing, directory grouping) in `scripts/generate_catalog.py`
- [x] T014 [US1] Implement `--check` flag for CI staleness detection in `scripts/generate_catalog.py`

### Documentation for User Story 1 (MANDATORY)

- [x] T015 [US1] Update `README.md` (or `docs/onboarding.md`) with instructions on running the catalog generator
**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Verify Policy Compliance (Priority: P2)

**Goal**: Provide a human-readable, always-current policy verification report in Backstage TechDocs.

**Independent Test**: Run policy verification tests and check that `docs/policy-verification/latest.md` is generated and renders correctly in MkDocs.

### Tests for User Story 2 (MANDATORY) ⚠️

- [x] T016 [P] [US2] Create unit test for Markdown report generation in `tests/unit/services/test_policy_verification_report.py`
- [x] T017 [P] [US2] Create integration test ensuring report is generated on test run in `tests/integration/policy/test_verification_lifecycle.py`

### Implementation for User Story 2

- [x] T018 [P] [US2] Update `src/domain/services/policy_verifier.py` (or service) to support Markdown output format
- [x] T019 [US2] Implement `generate_markdown_report` method using `scripts/templates/verification-report.md.j2`
- [x] T020 [US2] Update CI/Test runner hook (e.g., `conftest.py` or `pytest.ini` hooks) to trigger report generation after tests
- [x] T021 [US2] Configure `mkdocs.yml` (if present, or create task to add it) to include `docs/policy-verification/`

### Documentation for User Story 2 (MANDATORY)

- [x] T022 [US2] Update developer docs on how to view local governance reports

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T023 [P] Add `mkdocs.yml` navigation entry for "Governance"
- [x] T024 Verify CI pipeline configuration updates (if any manual steps required outside this repo)
- [x] T025 Run full end-to-end smoke test of catalog generation and report publishing locally

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (Catalog)**: Independent.
- **User Story 2 (Verification)**: Independent (uses separate service), but logically follows catalog in the governance "lens" concept.

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Templates/Contracts before Logic
- Logic before Integration
- Story complete before moving to next priority

### Parallel Opportunities

- T007, T008, T009 (US1 Tests) can run in parallel
- T010, T011, T012 (US1 Logic components) can run in parallel
- T016, T017 (US2 Tests) can run in parallel
- US1 and US2 implementation can effectively run in parallel once shared Jinja2 setup (T005) is done.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 & 2
2. Implement US1 (Catalog Generator)
3. Verify `catalog-info.yaml` output matches Backstage expectations
4. **STOP and VALIDATE**

### Incremental Delivery

1. Foundation
2. US1 (Catalog) -> Deploy to CI
3. US2 (Verification Report) -> Deploy to CI

---
