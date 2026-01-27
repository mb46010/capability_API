# Module Context: Domain Services

**AI Facts for Coding Agents**

## Purpose
Core business logic sanctuary. Orchestrates actions and flows without knowing about transport or storage implementations.

## Key Exports
- `ActionService`: Evaluates policies and routes short-lived deterministic operations to connectors.
- `FlowService`: Manages state and execution of long-running HR processes.
- `PolicyEngine`: Pure logic engine for capability-based authorization.

## Dependency Graph (Functional)
- **Imports**: `src.domain.entities.*`, `src.domain.ports.*`
- **Ports**: Consumes `ConnectorPort`, `FlowRunnerPort`, `PolicyLoaderPort`.

## Architectural Constraints
- MUST NOT import from `src.adapters.*` (Hexagonal core purity).
- MUST return `ActionResponse` or `FlowStatusResponse` entities.
- Policy evaluation is mandatory before any port execution.

## Local Gotchas
- Latency is calculated in the `ActionService` layer, not the connector.
- AI Agent field filtering happens in `ActionService.execute_action`.
