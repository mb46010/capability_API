# Module Context: Filesystem Adapters

**AI Facts for Coding Agents**

## Purpose
Implementation of ports that interact with the local disk.

## Key Exports
- `FilePolicyLoaderAdapter`: Loads YAML policies from disk.
- `LocalFlowRunnerAdapter`: Simulates flow execution using local state.

## Dependency Graph (Functional)
- **Imports**: `src.domain.entities.*`, `src.domain.ports.*`
- **Ports**: Implements `PolicyLoaderPort`, `FlowRunnerPort`.

## Architectural Constraints
- MUST NOT contain business logic.
- Path handling MUST be cross-platform compatible.
