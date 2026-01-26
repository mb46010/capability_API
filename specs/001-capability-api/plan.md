# Implementation Plan: Capability API

**Branch**: `001-capability-api` | **Date**: 2026-01-26 | **Spec**: [specs/001-capability-api/spec.md](specs/001-capability-api/spec.md)
**Input**: Feature specification from `specs/001-capability-api/spec.md`

## Summary

The HR AI Platform Capability API is a Python-based service acting as the central governance layer for AI agents and workflows. It exposes a versioned OpenAPI surface for deterministic **Actions** and long-running **Flows**. It enforces a strict **Policy-as-Code** model (defined in `schemas/policy-schema.json`), handles Identity via **Okta OIDC**, and abstracts infrastructure using a **Hexagonal Architecture** (local-first dev, cloud deployment).

**Key Integration**: The policy engine must implement the schema defined in `schemas/policy-schema.json` and follow the semantics in `schemas/policy-schema.md`.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: 
- `fastapi` (Web framework)
- `pydantic` (Data validation, V2)
- `pyyaml` (Policy parsing)
- `httpx` (Async HTTP client)
- `tenacity` (Retries)
- `python-jose` or `authlib` (OIDC/JWT handling)
**Storage**: 
- **Policy/Config**: Git-backed YAML files (read via File Adapter or S3 Adapter)
- **State/Audit**: Structured logs (File/CloudWatch) and potentially a lightweight state store for idempotency (File/DynamoDB)
**Testing**: `pytest`, `pytest-cov`, `pytest-asyncio`
**Target Platform**: Linux (Containerized), AWS Step Functions (for Flows)
**Project Type**: Service (API)
**Performance Goals**: <200ms p95 for Actions; Reliable async handoff for Flows.
**Constraints**: 
- Strict PII masking in logs.
- "Fail-fast" for connector failures.
- Idempotency for all actions.
**Scale/Scope**: Platform foundation; supports multiple concurrent agents/workflows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: Design separates `api` (primary adapter) and `adapters` (secondary) from `domain` logic via `ports`.
- [x] **Actions vs Flows**: Explicit separation in API design (sync vs async/callback).
- [x] **Python-Native**: Logic in pure Python; Pydantic for schemas.
- [x] **Observability**: Provenance logging is a core requirement (FR-001).
- [x] **Privacy & PII**: Logging middleware will enforce PII masking (Article VIII).
- [x] **Local Parity**: Local filesystem adapters for Policy/Storage; Mock adapters for Okta/Connectors.

## Project Structure

### Documentation (this feature)

```text
specs/001-capability-api/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── api/                 # Primary Adapter (FastAPI)
│   ├── routes/
│   ├── dependencies.py
│   └── main.py
├── domain/              # Core Logic (Ports & Entities)
│   ├── entities/        # Pydantic models (Policy, Action, Flow)
│   ├── services/        # Business logic (PolicyEngine, FlowRunner)
│   └── ports/           # Abstract Interfaces (Storage, Identity, Connector)
├── adapters/            # Secondary Adapters
│   ├── filesystem/      # Local file storage
│   ├── s3/              # AWS S3 storage (placeholder)
│   ├── okta/            # Identity provider (Real/Mock)
│   └── connectors/      # MCP/External system connectors
├── lib/                 # Shared utilities
│   ├── logging.py       # PII masking logger
│   └── security.py
└── main.py              # Entry point

tests/
├── integration/
├── unit/
└── conftest.py
```

**Structure Decision**: Hexagonal Architecture (Ports & Adapters) to ensure Local/Cloud parity and separation of concerns.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (None)    |            |                                     |