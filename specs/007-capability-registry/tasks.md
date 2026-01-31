# Tasks: Capability Registry

**Feature**: Capability Registry (`007-capability-registry`)
**Status**: Completed
**Spec**: [spec.md](spec.md)

## Implementation Strategy
- **MVP (Phase 3)**: Implement the Core Registry, Service, and Startup Validation (User Story 1). This ensures the server fails fast on configuration errors.
- **Increment 1 (Phase 4)**: Implement Runtime Validation (User Story 2) to enforce the registry during API requests and handle deprecations.
- **Increment 2 (Phase 5)**: Implement CLI tools (User Story 3) for developer ergonomics and CI/CD integration.
- **Testing**: TDD is mandatory. Each phase starts with a test creation task.

## Dependencies
- Phase 2 (Foundational) blocks all subsequent phases.
- Phase 3 (Startup Validation) blocks Phase 4 (Runtime Validation).
- Phase 5 (CLI) can technically run in parallel with Phase 4, but logically follows it.

## Phase 1: Setup

- [x] T001 Install `tabulate` dependency in requirements.txt

## Phase 2: Foundational (Blocking)

- [x] T002 Create initial registry file at config/capabilities/index.yaml with 13 capabilities
- [x] T003 Create Pydantic models for CapabilityEntry and CapabilityRegistry in src/domain/entities/capability.py
- [x] T004 Create README.ai.md for src/domain/entities/

## Phase 3: User Story 1 - Startup Policy Validation (P1)

**Goal**: Fail server startup if policy references unknown capabilities.

**Mandatory Tests**:
- Unit tests for `CapabilityRegistryService` (loading, wildcards, fuzzy search).
- Integration test for `FilePolicyLoaderAdapter` detecting invalid capabilities.

- [x] T005 [US1] Create unit tests for CapabilityRegistryService in tests/unit/domain/test_capability_registry.py
- [x] T006 [US1] Implement CapabilityRegistryService (loader, O(1) lookup, wildcards) in src/domain/services/capability_registry.py
- [x] T007 [US1] Integrate Registry with AppSettings validation in src/lib/config_validator.py
- [x] T008 [US1] Create integration tests for Policy Loader validation in tests/integration/test_policy_loader_registry.py
- [x] T009 [US1] Update FilePolicyLoaderAdapter to validate capabilities in src/adapters/filesystem/policy_loader.py
- [x] T010 [US1] Create README.ai.md for src/domain/services/

## Phase 4: User Story 2 - Runtime Request Validation (P2)

**Goal**: Validate API requests against registry and log warnings for deprecated capabilities.

**Mandatory Tests**:
- Integration test for `ActionService` returning 400 for unknown actions.
- Integration test for `ActionService` logging warning for deprecated actions.

- [x] T011 [US2] Create integration tests for ActionService runtime validation in tests/integration/test_action_service_registry.py
- [x] T012 [US2] Update ActionService to use CapabilityRegistryService in src/domain/services/action_service.py
- [x] T013 [US2] Implement deprecation warning logging in ActionService in src/domain/services/action_service.py

## Phase 5: User Story 3 - CLI Registry Management (P3)

**Goal**: Provide CLI tools for listing and validating capabilities.

**Mandatory Tests**:
- Test CLI `list` command output.
- Test CLI `check-policy` command with valid/invalid policies.

- [x] T014 [US3] Create tests for CLI script in tests/unit/scripts/test_capability_registry_cli.py
- [x] T015 [US3] Implement CLI script in scripts/capability-registry
- [x] T016 [US3] Add execute permissions to scripts/capability-registry
- [x] T017 [US3] Create Github Actions workflow for registry validation in .github/workflows/validate-registry.yml

## Phase 6: Polish & Cross-Cutting

- [x] T018 Create developer guide in docs/CAPABILITY_REGISTRY.md
- [x] T019 Update project README.md to reference Capability Registry
- [x] T020 Run full regression suite to ensure no existing flows are broken
