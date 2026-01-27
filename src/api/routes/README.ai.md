# Module Context: API Routes

**AI Facts for Coding Agents**

## Purpose
Entry points for HTTP requests. Handles request parsing, authentication injection, and response formatting.

## Key Exports
- `actions.router`: Endpoints for short-lived actions.
- `flows.router`: Endpoints for workflow management.

## Dependency Graph (Functional)
- **Imports**: `src.domain.services.*`, `src.api.dependencies`.
- **External**: `FastAPI`.

## Architectural Constraints
- MUST NOT contain business logic; delegate to `ActionService` or `FlowService`.
- MUST use `get_current_principal` dependency for authentication.
- MUST return `ActionResponse` or `FlowStatusResponse`.

## Local Gotchas
- The `/actions/{domain}/{action}` route is a generic gateway to the `ActionService`.
