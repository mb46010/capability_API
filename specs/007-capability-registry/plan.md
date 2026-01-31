# Implementation Plan - Capability Registry

**Feature**: Capability Registry (`007-capability-registry`)
**Status**: Draft
**Spec**: [spec.md](spec.md)

## Technical Context

<!--
  ACTION REQUIRED: Identify technical dependencies, integrations, and unknowns.
  Mark any unknowns as [NEEDS CLARIFICATION].
-->

- **Dependencies**:
    - `pydantic` (Data validation and schema definition)
    - `pyyaml` (Registry file parsing)
    - `difflib` (Fuzzy matching for typo detection)
    - `tabulate` (CLI output formatting, mentioned in PRD)

- **Integrations**:
    - **Configuration**: `src/lib/config_validator.py` (Startup validation)
    - **Policy**: `src/adapters/filesystem/policy_loader.py` (Validate references at startup)
    - **Runtime**: `src/domain/services/action_service.py` (Validate requests at runtime)
    - **CLI**: New script `scripts/capability-registry`

- **Architecture/Patterns**:
    - Singleton pattern for `CapabilityRegistryService` (via `functools.lru_cache` or dependency injection).
    - Monolithic YAML storage (`config/capabilities/index.yaml`) for Phase 1.
    - O(1) lookup map for performance.

- **Unknowns**:
    - [NEEDS CLARIFICATION] Confirm the existing logging configuration to ensure deprecation warnings follow the standard format (Article VIII).
    - [NEEDS CLARIFICATION] Verify exact import paths for `ActionService` and `PolicyLoader` to avoid circular dependencies (PRD hints at this risk).

## Constitution Check

<!--
  ACTION REQUIRED: Review the spec against the project constitution.
  Mark status as PASS, FAIL, or PENDING.
-->

- **[PASS] Article I: Python-Native**: Implementation uses idiomatic Python (Pydantic, standard libs).
- **[PASS] Article II: Hexagonal Integrity**: Registry data is loaded via a specific service; file access should ideally be an adapter, but for Phase 1/Option C, loading a config file directly in a service or via a config provider is acceptable "pragmatic" debt, provided the domain logic (validation) is pure.
- **[PASS] Article III: Operational Rigor**: Registry is read-only (idempotent).
- **[PASS] Article IV: Development Standards**: Plan includes TDD (tests first).
- **[PASS] Article V: Configuration**: Path to registry is configurable via `AppSettings`.
- **[PASS] Article VIII: Logging**: Deprecation warnings will use structured logging, not print.

## Gate Evaluation

<!--
  ACTION REQUIRED: Evaluate if the plan is ready to proceed.
  - [ ] Requirements are clear?
  - [ ] Constitution is satisfied?
  - [ ] Unknowns are identified and planned for research?
-->

- **Status**: **GO** (Pending Research)
- **Notes**: Proceed to Phase 0 to verify logging patterns and path structures.

## Phases

### Phase 0: Outline & Research

<!--
  Goal: Resolve unknowns and validate design assumptions.
-->

- [ ] **Research Task 1**: Inspect `src/lib/logging.py` (or equivalent) to understand the standard logging pattern for warning messages.
- [ ] **Research Task 2**: Verify the directory structure and existing dependencies of `src/domain/services/action_service.py` and `src/adapters/filesystem/policy_loader.py` to plan for circular dependency avoidance.
- [ ] **Research Task 3**: Confirm `tabulate` is in `requirements.txt` or needs to be added.
- [ ] **Deliverable**: `research.md` with decisions on logging, imports, and dependencies.

### Phase 1: Core Implementation (Registry & Service)

<!--
  Goal: Implement the data model, registry file, and the service to load it.
-->

- [ ] **Task 1.1**: Create `config/capabilities/index.yaml` with the initial 13 capabilities.
- [ ] **Task 1.2**: Create `src/domain/entities/capability.py` with Pydantic models (`CapabilityEntry`, `CapabilityRegistry`).
- [ ] **Task 1.3**: Implement `src/domain/services/capability_registry.py` with loading logic, O(1) lookup, wildcard matching, and fuzzy search.
    - *Test First*: Create `tests/unit/domain/test_capability_registry.py`.
- [ ] **Task 1.4**: Integrate with `src/lib/config_validator.py` to validate registry existence at startup.
- [ ] **Deliverable**: Working Registry Service with unit tests and valid YAML file.

### Phase 2: Integrations (Policy, Runtime, CLI)

<!--
  Goal: Enforce the registry in PolicyLoader, ActionService, and provide CLI tools.
-->

- [ ] **Task 2.1**: Update `src/adapters/filesystem/policy_loader.py` to validate capabilities against the registry.
    - *Test First*: Update/Create integration tests for policy loading with invalid capabilities.
- [ ] **Task 2.2**: Update `src/domain/services/action_service.py` to validate runtime requests and log deprecation warnings.
    - *Test First*: Integration test for runtime validation failures and warning logs.
- [ ] **Task 2.3**: Implement `scripts/capability-registry` CLI tool.
- [ ] **Task 2.4**: Add `scripts/capability-registry validate` and `check-policy` to CI/CD (GitHub Actions / pre-commit).
- [ ] **Deliverable**: Full feature complete with end-to-end enforcement and tooling.

### Phase 3: Documentation & Handoff

<!--
  Goal: Finalize documentation and verify all standards.
-->

- [ ] **Task 3.1**: Create `docs/CAPABILITY_REGISTRY.md` (Developer Guide).
- [ ] **Task 3.2**: Update `README.md` to reference the new registry.
- [ ] **Task 3.3**: Ensure all new modules have `README.ai.md`.
- [ ] **Deliverable**: Complete documentation.