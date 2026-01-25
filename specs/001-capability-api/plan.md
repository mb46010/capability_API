# Implementation Plan: HR AI Platform Capability API

**Branch**: `001-capability-api` | **Date**: 2026-01-25 | **Spec**: [specs/001-capability-api/spec.md]
**Input**: Feature specification from `/specs/001-capability-api/spec.md`

## Summary
Build a governed HR AI Platform centered around a Capability API. The system uses a hexagonal architecture to remain storage-agnostic (Local FS vs S3) and implements a capability-based authorization model using Okta OIDC and a curated policy YAML. Long-running HR processes (Flows) are orchestrated via AWS Step Functions (simulated locally).

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic V2, Authlib (tentative), MCP SDK
**Storage**: Storage Port (Local Filesystem adapter for development, S3 adapter for cloud)
**Testing**: pytest
**Target Platform**: Linux / AWS
**Project Type**: Single (API-centric)
**Performance Goals**: Deterministic action execution, <200ms API overhead
**Constraints**: Capability-based auth, policy YAML enforcement, local-first parity
**Scale/Scope**: Managed access to HR data via MCP connectors

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: Design uses Storage Port to abstract persistence.
- [x] **Actions vs Flows**: Explicitly defined in spec (Short vs Long-running).
- [x] **Python-Native**: Built with FastAPI/Pydantic.
- [x] **Observability**: Audit trails with provenance are part of the Action schema.
- [x] **Local Parity**: Full local execution with mock Okta and mock Flow runner.

## Project Structure

### Documentation (this feature)

```text
specs/001-capability-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── api/                 # Capability API (FastAPI)
├── core/                # "Signal Engine" business logic
├── adapters/
│   ├── storage/         # Local FS / S3 adapters
│   ├── flows/           # Mock runner / AWS Step Functions
│   └── auth/            # Okta OIDC validation
├── connectors/          # MCP Client wrappers
├── policy/              # YAML policy engine
└── models/              # Pydantic schemas

tests/
├── unit/
├── integration/
└── contract/            # OpenAPI contract validation
```

**Structure Decision**: Option 1 (Single project) with a strong internal package structure to maintain Hexagonal Integrity.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |