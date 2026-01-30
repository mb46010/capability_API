# Filesystem Adapters

Implementation of ports that interact with the local disk. These adapters provide persistence and execution capabilities using the local filesystem.

## Key Components

- **FilePolicyLoaderAdapter**: Loads YAML policies from disk.
- **LocalFlowRunnerAdapter**: Simulates flow execution using local state.

## Implementation Details

- **Ports**: Implements `PolicyLoaderPort` and `FlowRunnerPort`.
- **Dependencies**: `src.domain.entities.*`, `src.domain.ports.*`.

## Constraints

- MUST NOT contain business logic.
- Path handling MUST be cross-platform compatible.
