# Tasks: Capability API

**Feature**: `001-capability-api`
**Status**: Planned
**Spec**: [specs/001-capability-api/spec.md](specs/001-capability-api/spec.md)

## Phase 1: Setup
*Goal: Initialize project structure and dependencies.*

- [X] T001 Create Python virtual environment and install dependencies (fastapi, uvicorn, pydantic, pyyaml, httpx, tenacity, authlib) in `requirements.txt`
- [X] T002 Create project directory structure (src/api, src/domain, src/adapters, src/lib, tests) per `plan.md`
- [X] T003 [P] Configure `pyproject.toml` or `pytest.ini` for testing configuration
- [X] T004 [P] Create `.env.example` with required environment variables (LOG_LEVEL, POLICY_PATH, OKTA_ISSUER)
- [X] T005 Create `src/main.py` entry point with basic FastAPI app shell

## Phase 2: Foundational (US1 - Policy Engine)
*Goal: Implement the core Python-native policy engine to validate permissions.*
*Prerequisites: Phase 1*

### Independent Test Criteria
- Unit tests verify `PolicyEngine` correctly evaluates `ALLOW`/`DENY` based on `policy-schema.json` rules.
- Tests cover wildcard matching, environment filtering, and principal resolution.

### Tasks
- [X] T006 [US1] Create mandatory tests for Policy Engine logic in `tests/unit/test_policy_engine.py`
- [X] T007 [P] [US1] Implement Pydantic models for Policy entities in `src/domain/entities/policy.py` matching `data-model.md`
- [X] T008 [US1] Implement `PolicyLoader` port and file adapter in `src/adapters/filesystem/policy_loader.py` to read YAML
- [X] T009 [US1] Implement `PolicyEngine` service in `src/domain/services/policy_engine.py` with evaluation logic (precedence, wildcards)
- [X] T010 [US1] Create sample `config/policy.yaml` for local development/testing

## Phase 3: User Story 2 - Action Execution
*Goal: Execute short-lived actions via API with provenance and MCP integration.*
*Prerequisites: Phase 2*

### Independent Test Criteria
- Integration tests verify `/actions/{domain}/{action}` returns 200 OK with valid policy.
- Tests verify 403 Forbidden when policy denies access.
- Tests verify response contains "JSON with Provenance" structure.

### Tasks
- [X] T011 [US2] Create mandatory contract tests for Action endpoints in `tests/integration/test_action_routes.py`
- [X] T012 [P] [US2] Implement `ActionRequest` and `ActionResponse` models in `src/domain/entities/action.py`
- [X] T013 [P] [US2] Define `ConnectorPort` interface in `src/domain/ports/connector.py`
- [X] T014 [US2] Implement `MockConnectorAdapter` in `src/adapters/connectors/mock_connector.py` for testing (simulating MCP)
- [X] T015 [US2] Implement `ActionService` in `src/domain/services/action_service.py` integrating Policy check and Connector call
- [X] T016 [US2] Implement FastAPI routes for actions in `src/api/routes/actions.py`
- [X] T017 [US2] Register action routes in `src/api/main.py`

## Phase 4: User Story 3 - Flow Orchestration
*Goal: Trigger and track long-running flows using a local runner.*
*Prerequisites: Phase 3*

### Independent Test Criteria
- Integration tests verify `/flows/...` endpoints for start and status.
- Tests verify FlowRunner correctly handles state transitions (mocked).

### Tasks
- [X] T018 [US3] Create mandatory tests for FlowRunner logic in `tests/unit/test_flow_runner.py`
- [X] T019 [P] [US3] Implement `FlowStartRequest` and `FlowStatusResponse` models in `src/domain/entities/flow.py`
- [X] T020 [US3] Define `FlowRunnerPort` interface in `src/domain/ports/flow_runner.py`
- [X] T021 [US3] Implement `LocalFlowRunnerAdapter` in `src/adapters/filesystem/local_flow_runner.py` (in-memory/file state)
- [X] T022 [US3] Implement FastAPI routes for flows in `src/api/routes/flows.py`
- [X] T023 [US3] Register flow routes in `src/api/main.py`

## Phase 5: User Story 4 - Security & Observability
*Goal: Secure the API and ensure PII masking in logs.*
*Prerequisites: Phase 4*

### Independent Test Criteria
- Tests verify PII (e.g., email) is masked in logs.
- Tests verify requests without valid OIDC tokens are rejected (401).

### Tasks
- [X] T024 [US4] Create mandatory tests for PII masking and Auth middleware in `tests/unit/test_security.py`
- [X] T025 [P] [US4] Implement PII masking formatter in `src/lib/logging.py`
- [X] T026 [US4] Implement Mock OIDC/Auth middleware in `src/api/dependencies.py` to simulate Okta
- [X] T027 [US4] Apply Auth dependency to all API routes
- [X] T028 [US4] Verify "JSON with Provenance" output across all endpoints

## Phase 6: Polish & Cross-Cutting
*Goal: Documentation and final cleanup.*

- [X] T029 Create `README.md` with instructions from `quickstart.md`
- [X] T030 Ensure `openapi.yaml` matches the generated FastAPI OpenAPI schema
- [X] T031 Run full test suite and ensure 95%+ coverage
- [X] T032 Clean up temporary files and verified artifacts

## Dependencies

1.  **US1 (Policy)**: Foundation for all access control. Must be first.
2.  **US2 (Actions)**: depends on US1.
3.  **US3 (Flows)**: depends on US1. Can be parallel with US2, but simpler to do after Action patterns are established.
4.  **US4 (Security)**: Wraps US2 and US3. Can be developed in parallel, but integration happens last to avoid blocking dev flow.

## Implementation Strategy

1.  **MVP**: Complete Phase 1 & 2 + T015/T016 (Basic Action execution with Mock Policy).
2.  **Alpha**: Complete Phase 3 (Connectors) & Phase 4 (Flows).
3.  **Beta**: Complete Phase 5 (Security/PII) for "Production-Ready" local status.
