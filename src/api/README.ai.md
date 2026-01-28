# Module Context: src/api

**AI Facts for Coding Agents**

## Purpose
The API layer serves as the entry point for the HR AI Platform. It defines the FastAPI application, routes, and shared dependencies for both deterministic Actions and long-running Flows.

## Key Exports
- `app`: The main FastAPI application instance (in `src/main.py` but configured here).
- `get_current_principal`: Dependency for extracting OIDC identity from headers.
- `get_policy_engine`: Dependency providing access to the centralized policy evaluator.
- `get_connector`: Dependency providing access to the Workday Simulator or external ports.

## Dependency Graph (Functional)
- **Imports**: `src.domain.services`, `src.adapters.auth`, `src.domain.entities`
- **Ports**: `ConnectorPort`, `FlowRunnerPort`
- **External**: `fastapi`, `uvicorn`, `authlib`

## Architectural Constraints
- **Identity First**: Every route MUST use `Depends(get_current_principal)` unless explicitly public (e.g., `/health`).
- **Policy Governed**: Business logic MUST NOT perform raw auth checks; use `PolicyEngine` via `ActionService`.
- **Response Envelopes**: All actions MUST return `ActionResponse` to ensure consistent audit trails (provenance).

## Local Gotchas
- **OIDC Mocking**: In local mode, the `MockOktaProvider` accepts any token but relies on the `subject` claim for permission mapping.
- **Async Required**: All route handlers and service methods are `async`.
