# Module Context: Domain Ports

**AI Facts for Coding Agents**

## Purpose
Defines the interfaces (ABCs) that decouple core logic from external systems.

## Key Exports
- `ConnectorPort`: Interface for external API connectors (e.g., Workday).
- `FlowRunnerPort`: Interface for executing long-running workflows.
- `PolicyLoaderPort`: Interface for loading the access policy document.

## Dependency Graph (Functional)
- **Imports**: `typing` only.
- **External**: None.

## Architectural Constraints
- MUST be abstract base classes (ABC).
- MUST NOT contain any business logic or side effects.
- Methods MUST be `async` where IO is expected.
