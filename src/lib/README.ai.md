# Module Context: Common Utilities

**AI Facts for Coding Agents**

## Purpose
Shared helper functions and generic tools used across the project.

## Key Exports
- `logging`: Standardized logging configuration with PII masking support.

## Dependency Graph (Functional)
- **External**: Python standard library (`logging`, `json`).

## Architectural Constraints
- MUST NOT depend on domain logic or adapters.
- Functions MUST be pure where possible.
- PII masking MUST be applied to log outputs.
