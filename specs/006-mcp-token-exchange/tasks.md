# Tasks: MCP Token Exchange

**Feature Branch**: `006-mcp-token-exchange`
**Status**: Completed

## Implementation Strategy

We will implement this feature in phases corresponding to the prioritized user stories.
- **Phase 1**: Setup (Project configuration)
- **Phase 2**: Foundational (Blocking prerequisites - none for this feature)
- **Phase 3 (User Story 1)**: Secure Token Exchange (The core mechanism)
- **Phase 4 (User Story 2)**: Scope-Based Access Enforcement (The security barrier)
- **Phase 5 (User Story 3)**: Sensitive Action Freshness (Enhanced security rule)
- **Phase 6 (User Story 4)**: Provenance Audit (Observability)
- **Phase 7**: Polish & Cross-Cutting Concerns

Tests are **MANDATORY** and must be written *before* implementation (TDD).

---

## Phase 1: Setup

- [x] T001 Create feature branch `006-mcp-token-exchange` (already done)
- [x] T002 Ensure local environment is ready (install dependencies)

---

## Phase 2: Foundational

*No blocking foundational tasks identified. Proceeding directly to User Stories.*

---

## Phase 3: User Story 1 - Secure Token Exchange (Priority: P1)

**Goal**: Enable the MCP Server to exchange a long-lived user token for a short-lived, scoped MCP token.

**Independent Test Criteria**: A call to `MockOktaProvider.exchange_token` with a valid user token returns a new token with 5-minute TTL, `mcp:use` scope, and correct provenance claims.

### Mandatory Tests
- [x] T003 [US1] Create unit test file `tests/unit/adapters/auth/test_mock_okta_exchange.py`
- [x] T004 [US1] Write test: `test_exchange_token_success` (verify TTL, scope, provenance)
- [x] T005 [US1] Write test: `test_exchange_token_rejects_nested` (chain of chains)
- [x] T006 [US1] Write test: `test_exchange_token_missing_authtime` (fallback to iat)

### Implementation
- [x] T007 [US1] Implement `exchange_token` method in `src/adapters/auth/mock_okta.py`
- [x] T008 [US1] Update `token` endpoint in `src/adapters/auth/mock_okta.py` to handle `urn:ietf:params:oauth:grant-type:token-exchange`
- [x] T009 [US1] Verify tests pass for MockOkta extension

### Integration (MCP Side)
- [x] T010 [US1] Create integration test `tests/integration/mcp/test_mcp_token_flow.py`
- [x] T011 [US1] Implement `get_mcp_token` with **caching** in `src/mcp/adapters/auth.py`
- [x] T012 [US1] Refactor `src/mcp/tools/hcm.py` to use `get_mcp_token`
- [x] T013 [P] [US1] Refactor `src/mcp/tools/time.py` to use `get_mcp_token`
- [x] T014 [P] [US1] Refactor `src/mcp/tools/payroll.py` to use `get_mcp_token`
- [x] T015 [US1] Verify all MCP tools use exchanged tokens via tests

---

## Phase 4: User Story 2 - Scope-Based Access Enforcement (Priority: P1)

**Goal**: Prevent direct API access using MCP-scoped tokens unless authorized via specific context.

**Independent Test Criteria**: A request to `ActionService` with a token containing `mcp:use` scope but missing `acting_as` context is rejected with 403.

### Mandatory Tests
- [x] T016 [US2] Create unit test file `tests/unit/domain/test_policy_engine_scope.py`
- [x] T017 [US2] Write test: `test_policy_enforces_required_scope`
- [x] T018 [US2] Create integration test `tests/integration/test_security_boundaries.py`
- [x] T019 [US2] Write test: `test_direct_api_access_with_mcp_token_rejected`

### Implementation
- [x] T020 [US2] Update `PolicyConditions` schema in `src/domain/entities/policy.py` to add `required_scope`
- [x] T021 [US2] Update `_evaluate_conditions` in `src/domain/services/policy_engine.py` to check `required_scope`
- [x] T022 [US2] Update `ActionService.execute_action` in `src/domain/services/action_service.py` to reject `mcp:use` without `acting_through`
- [x] T023 [US2] Verify tests pass for scope enforcement

---

## Phase 5: User Story 3 - Sensitive Action Freshness (Priority: P2)

**Goal**: Enforce recent authentication (Step-Up) for sensitive capabilities.

**Independent Test Criteria**: A request with an `auth_age` > `max_auth_age_seconds` is rejected.

### Mandatory Tests
- [x] T024 [US3] Add test to `tests/unit/domain/test_policy_engine_scope.py`: `test_policy_enforces_max_auth_age`
- [x] T025 [US3] Add test case: `test_freshness_check_handles_missing_auth_time`

### Implementation
- [x] T026 [US3] Update `PolicyConditions` schema in `src/domain/entities/policy.py` to add `max_auth_age_seconds`
- [x] T027 [US3] Update `_evaluate_conditions` in `src/domain/services/policy_engine.py` to check `auth_time` vs current time
- [x] T028 [US3] Verify tests pass for freshness checks

---

## Phase 6: User Story 4 - Provenance Audit (Priority: P2)

**Goal**: Ensure audit logs capture the full token chain and actor context.

**Independent Test Criteria**: Audit log entries for MCP actions contain `acting_through`, `original_token_id`, and `token_scope`.

### Mandatory Tests
- [x] T029 [US4] Update `tests/integration/test_audit_routes.py` or similar to verify log content fields
- [x] T030 [US4] Write test: `test_audit_log_contains_provenance_fields`

### Implementation
- [x] T031 [US4] Update `log_event` signature in `src/adapters/filesystem/logger.py` to accept token metadata
- [x] T032 [US4] Update call sites in `ActionService` to pass token metadata to logger
- [x] T033 [US4] Verify audit logs in `logs/` (or temp test logs) contain new fields

---

## Phase 7: Polish & Cross-Cutting Concerns

- [x] T034 Create demo script `scripts/demo/token_exchange_demo.sh`
- [x] T035 Update `docs/security_architecture.md` (if exists) or create `docs/modules/token_exchange.md` with new flow details
- [x] T036 Run full regression suite `pytest`
- [x] T037 Check for any PII leaks in new log fields

## Dependencies

- Phase 4 depends on Phase 3 (needs MCP tokens to test rejection).
- Phase 6 depends on Phase 3 (needs metadata from exchanged tokens).
- Phase 5 is independent but fits best after core policy engine changes in Phase 4.

## Parallel Execution

- T013, T014 (MCP Tool Refactoring) can be done in parallel once T011 is complete.
- Phase 5 (Freshness) can be implemented in parallel with Phase 4 (Scope) as they touch the same files but different logic paths.