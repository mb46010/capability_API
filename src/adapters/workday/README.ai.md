# Module Context: Workday Adapter

**AI Facts for Coding Agents**

## Purpose
Simulated Workday connector for development and testing. Provides HCM, Time Tracking, and Payroll operations.

## Key Exports
- `WorkdaySimulator`: Implementation of `ConnectorPort`.
- `WorkdaySimulationConfig`: Configuration for latency and failure injection.

## Dependency Graph (Functional)
- **Imports**: `src.adapters.workday.domain.*`, `src.adapters.workday.services.*`, `src.adapters.workday.loader`.
- **Ports**: Implements `ConnectorPort`.
- **External**: `PyYAML`, `Pydantic`.

## Architectural Constraints
- State is in-memory only and resets on restart.
- MUST load data from YAML fixtures in `src/adapters/workday/fixtures/`.
- MUST simulate realistic latency profiles (50-500ms).

## Local Gotchas
- Dates in YAML are strings; Pydantic handles conversion.
- Manager references are resolved in a two-pass load in `loader.py`.
