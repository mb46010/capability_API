# Tasks: Mock Scenarios Implementation

**Feature**: `001-capability-api` (Mock Scenarios Enhancement)
**Status**: Planned
**Spec**: [specs/001-capability-api/spec.md](specs/001-capability-api/spec.md)

## Phase 1: Setup & Configuration
*Goal: Prepare the environment with necessary data and policy rules.*

- [X] T101 Update `config/policy.yaml` with the complex policy definitions provided in the user request (Test Data Fixtures).
- [X] T102 [P] Create `tests/integration/conftest.py` (if not exists) or update it to support the new scenarios (e.g., fixtures for tokens).

## Phase 2: Mock Connector Enhancement
*Goal: Make the mock connector realistic with data fixtures and delays.*

- [X] T103 Enhance `src/adapters/connectors/mock_connector.py` to support in-memory Employee DB (CRUD).
- [X] T104 Add `time.sleep()` delays to `MockConnectorAdapter` methods to simulate realistic latency.
- [X] T105 Implement "Failure Injection" capability in `MockConnectorAdapter` (e.g. trigger errors based on input IDs).

## Phase 3: Scenario Implementation (Integration Tests)
*Goal: Implement the scenarios as executable tests.*

- [X] T106 [US1] Implement Scenario 1 (Employee Lookup) tests in `tests/integration/test_scenarios.py`.
    - 1.1 Admin Full Access
    - 1.2 AI Agent Limited Access (Field filtering logic needed in Connector or Service?) -> *Note: Connector should likely return full data, Service/Policy might filter, OR Connector filters based on caller. For MVP, Service/Adapter logic update might be needed.* **Decision**: Implement field filtering in `MockConnectorAdapter` based on principal role/type passed in context (if available) or assume Policy check limits access to specific "views" (e.g. `get_employee_public` vs `get_employee_full`). *Refinement*: The Spec 1.2 says "Response contains LIMITED employee record". The `ActionService` just passes data through. We'll simulate this by having the Connector return different data or the Service filtering. Let's make the Connector smart enough for this mock.
    - 1.3 AI Agent Denied Compensation
    - 1.4 Unauthorized Denied
    - 1.5 Machine Workflow Scoped Access
- [X] T107 [US3] Implement Scenario 2 (Onboarding Flow) tests in `tests/integration/test_scenarios.py`.
    - 2.1 Machine triggers flow & status check
    - 2.2 AI Agent denied
    - 2.3 Admin triggers flow
    - 2.4 Flow state transitions (Simulate via FlowRunner internals or helper)
    - 2.5 Flow failure handling
- [X] T108 [US4] Implement Scenario 3 (Auth & Token Lifecycle) tests in `tests/integration/test_scenarios.py`.
    - 3.1 Valid token
    - 3.2 Expired token
    - 3.3 Revoked token
    - 3.4 TTL enforcement
    - 3.5 MFA missing
    - 3.6 Tampered token
- [X] T109 [US2] Implement Scenario 4 (Provenance) tests in `tests/integration/test_scenarios.py`.
    - 4.1 Provenance structure
    - 4.2 Audit levels
- [X] T110 [US2] Implement Scenario 5 (Edge Cases) tests in `tests/integration/test_scenarios.py`.
    - 5.1 Non-existent employee
    - 5.2 Connector timeout
    - 5.3 Malformed request
    - 5.4 Unknown capability
    - 5.5 Flow not found

## Phase 4: Refinement
*Goal: Ensure all tests pass and implementation details match requirements.*

- [X] T111 Verify all new tests pass with `pytest tests/integration/test_scenarios.py`.
- [X] T112 Ensure existing tests still pass.