# Implementation Plan - MCP Token Exchange

## 1. Technical Context

- **Language**: Python 3.11+
- **Frameworks**: FastAPI, Pydantic, PyJWT
- **Existing Components**: 
    - `src/adapters/auth/mock_okta.py` (Mock OIDC Provider)
    - `src/domain/services/policy_engine.py` (Authorization Logic)
    - `src/mcp/server.py` (MCP Server & Tooling)
    - `src/domain/services/action_service.py` (Direct API Entrypoint)

## 2. Constitution Check

- **Mission**: Aligns with "Governed Capability API" by enforcing strict security boundaries for agents.
- **Article I**: Token exchange is an **Action** (deterministic).
- **Article III**: Provenance tracking (`acting_as`) directly supports the Audit Trail.
- **Article IV**: Tests will be written first (TDD).
- **Article V**: Configurable TTLs and Policy Rules.
- **Article VIII**: Logging will be enhanced with PII-safe token metadata.

## 3. Phase 0: Research & Decisions

- **RFC 8693 Implementation**: Manual implementation in `MockOktaProvider` (lighter weight than Authlib server).
- **Token Caching**: **Mandatory** in MCP Server (4 min TTL).
- **Policy Schema**: Extended with `required_scope` and `max_auth_age_seconds`.
- **Nesting**: Explicitly **Rejected**.

## 4. Phase 1: Design

- **Data Model**: Defined in `data-model.md`.
    - New `Exchanged Token` entity structure.
    - Updated `PolicyConditions` schema.
- **API Contracts**: Defined in `contracts/mock-okta.yaml`.
    - Added `urn:ietf:params:oauth:grant-type:token-exchange` support.

## 5. Phase 2: Implementation Steps

### Step 1: MockOkta Extension (TDD)
- **Test**: `tests/unit/adapters/auth/test_mock_okta_exchange.py`
    - Verify RFC 8693 request parsing.
    - Verify TTL reduction (5 min).
    - Verify claim copying (`auth_time`, `sub`) and additions (`acting_as`, `original_token_id`).
    - Verify rejection of nested tokens.
- **Code**: `src/adapters/auth/mock_okta.py`
    - Implement `exchange_token` method.
    - Update `token` endpoint handler.

### Step 2: Policy Engine Updates (TDD)
- **Test**: `tests/unit/domain/test_policy_engine_scope.py`
    - Verify `required_scope` enforcement.
    - Verify `max_auth_age_seconds` enforcement.
- **Code**: `src/domain/entities/policy.py`
    - Update `PolicyConditions` model.
- **Code**: `src/domain/services/policy_engine.py`
    - Implement validation logic in `_evaluate_conditions`.

### Step 3: MCP Server Integration (TDD)
- **Test**: `tests/integration/mcp/test_mcp_token_flow.py`
    - Mock the exchange endpoint.
    - Verify MCP server requests exchange before tool call.
    - Verify caching behavior (second call uses cached token).
- **Code**: `src/mcp/adapters/auth.py`
    - Implement `get_mcp_token` with caching logic.
- **Code**: `src/mcp/tools/*.py` (Refactor)
    - Update tool wrappers to use `get_mcp_token`.

### Step 4: Audit & Direct Access Protection
- **Test**: `tests/integration/test_security_boundaries.py`
    - Attempt direct API call with MCP token -> Expect 403.
    - Verify audit log contains new fields.
- **Code**: `src/domain/services/action_service.py`
    - Add check: if `mcp:use` in scope and not `acting_through`, reject.
- **Code**: `src/adapters/filesystem/logger.py`
    - Update `log_event` to extract and log token metadata.

## 6. Verification Plan

- **Automated**: Run `pytest tests/unit tests/integration`
- **Manual**: Run `scripts/demo/token_exchange_demo.sh` (to be created) and verify audit logs.