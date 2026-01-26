# Implementation Plan: Mock Scenarios

**Branch**: `001-capability-api` | **Date**: 2026-01-27 | **Spec**: [specs/001-capability-api/spec.md](specs/001-capability-api/spec.md)
**Input**: User Request for `002-mock-scenarios`

## Summary

Implement a comprehensive suite of mock scenarios to validate the Capability API's behavior in realistic end-to-end workflows. This involves enhancing the `MockConnectorAdapter` to support data fixtures and simulated delays, updating the `policy.yaml` to reflect complex permission models, and writing a new integration test suite `tests/integration/test_scenarios.py` covering Employee Lookup, Onboarding Flow, Authentication Lifecycle, Provenance, and Edge Cases.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `pytest`, `httpx`
**Storage**: In-memory (Mock Connector), YAML (Policy)
**Testing**: `pytest` integration tests
**Project Type**: Service (API)
**Performance Goals**: N/A (Mocked)
**Constraints**: Must use `time.sleep` for realistic delays in mocks as requested.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: Enhancements remain within `adapters/` and `tests/`. Domain logic is untouched.
- [x] **Actions vs Flows**: Scenarios explicitly test both.
- [x] **Python-Native**: All mocks and tests in Python.
- [x] **Observability**: Verifies provenance and audit logging in scenarios.
- [x] **Privacy & PII**: Verifies PII masking and sensitive data handling (salary/SSN).
- [x] **Local Parity**: Purely local execution using mocks.

## Project Structure

### Documentation (this feature)

```text
specs/001-capability-api/
├── plan.md              # This file
├── research.md          # Re-used
├── data-model.md        # Re-used
└── tasks.md             # New tasks for scenarios
```

### Source Code (repository root)

```text
src/
├── adapters/
│   └── connectors/
│       └── mock_connector.py  # ENHANCE: Add data fixtures and delays
tests/
└── integration/
    └── test_scenarios.py      # NEW: Comprehensive scenario suite
config/
└── policy.yaml                # UPDATE: Add complex policies
```

**Structure Decision**: Enhance existing adapters and add a new integration test file.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None)    |            |                                     |