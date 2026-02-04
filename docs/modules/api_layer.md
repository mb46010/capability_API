# API Layer

The API layer is the public surface of the HR AI Platform. It is designed to be consumed by diverse clients including AI agents, web applications, and automated workflows.

## Design Philosophy

1.  **Uniformity**: Whether an operation is read-only (query) or state-mutating (action), it follows the same request/response pattern.
2.  **Governance**: No action can be executed without a valid OIDC token and a matching entry in the `policy.yaml`.
3.  **Auditability**: Every response contains a `meta.provenance` block identifying who did what and when.

## Core Components

### 1. Routes (`/routes`)
- **Actions**: Atomic, synchronous HR operations (e.g., `get_employee`, `request_time_off`).
- **Flows**: Triggers for multi-step HR processes (e.g., `onboarding`).
- **Audit**: Administrative endpoints for inspecting platform events (e.g., `/audit/recent`).

### 2. Dependencies (`dependencies.py`)
Centralized logic for:
- Authentication (OIDC/JWT validation)
- Authorization (Policy Engine injection)
- Infrastructure Ports (Connectors, Flow Runners)

### 3. Idempotency (`X-Idempotency-Key`)
The API supports request deduplication via the `X-Idempotency-Key` header.
- **Scope**: Deduplication is scoped to the tuple of `(Principal, Action, IdempotencyKey)`. This prevents "key theft" where one user's key could accidentally trigger a cached response for another user's different action.
- **Handling**: The `ActionService` passes the key down to the adapters. In the Workday Simulator, this is managed by an LRU cache with TTL eviction.

## Execution Flow

1.  **Request**: Client sends POST to `/actions/{domain}/{action}`.
2.  **Auth**: `get_current_principal` validates the JWT and extracts `VerifiedPrincipal` (preserving raw claims for scope validation).
3.  **Authorization**: `ActionService` asks `PolicyEngine` if the principal is allowed to invoke the capability.

4.  **Execution**: `ActionService` calls the appropriate adapter (e.g., `WorkdaySimulator`).
5.  **Response**: Result is wrapped in `ActionResponse` with execution metadata.

## Key Exports

- `app`: The main FastAPI application instance.
- `get_current_principal`: Dependency for extracting OIDC identity from headers.
- `get_policy_engine`: Dependency providing access to the centralized policy evaluator.
- `get_connector`: Dependency providing access to the Workday Simulator or external ports.

## Architectural Constraints

- **Identity First**: Every route MUST use `Depends(get_current_principal)` unless explicitly public (e.g., `/health`).
- **Policy Governed**: Business logic MUST NOT perform raw auth checks; use `PolicyEngine` via `ActionService`.
- **Response Envelopes**: All actions MUST return `ActionResponse` to ensure consistent audit trails (provenance).
