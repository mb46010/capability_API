# Implementation Plan: HR Platform MCP Server

**Branch**: `005-hr-mcp-server` | **Date**: 2026-01-30 | **Spec**: [specs/005-hr-mcp-server/spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-hr-mcp-server/spec.md`

## Summary
Implement a governed HR MCP server using FastMCP 3.0 that acts as a secure gateway to the Capability API. The server provides role-based tool discovery, enforces MFA for payroll actions, and ensures auditable execution with PII masking.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastMCP >= 3.0.0b1, httpx, pydantic-settings, PyJWT (for token inspection)
**Storage**: N/A (Stateless adapter/gateway)
**Testing**: pytest, pytest-asyncio, pytest-mock
**Target Platform**: Linux server / Containerized
**Project Type**: Single project (MCP Server)
**Performance Goals**: < 100ms latency for tool execution (excluding backend)
**Constraints**: < 100MB memory footprint, Stateless passthrough
**Scale/Scope**: 11 core HR tools (HCM, Time, Payroll)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: Yes, the MCP server is a Protocol Adapter (Adapter layer) in the hexagonal architecture.
- [x] **Actions vs Flows**: Yes, this is an ACTION-based interface for HR capabilities.
- [x] **Python-Native**: Yes, using FastMCP 3.0 and standard library.
- [x] **Observability**: Yes, provenance logging and audit trails are defined (FR-010).
- [x] **Privacy & PII**: Yes, PII masking is mandatory in logs (Article VIII).
- [x] **Local Parity**: Yes, connecting to local Capability API via .env configuration.

## Project Structure

### Documentation (this feature)

```text
specs/005-hr-mcp-server/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── openapi.yaml     # MCP Tool schema representation
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── mcp/
│   ├── __init__.py
│   ├── server.py        # FastMCP entry point
│   ├── tools/           # Domain-specific tool modules
│   │   ├── hcm.py
│   │   ├── time.py
│   │   └── payroll.py
│   ├── adapters/        # External interfaces
│   │   ├── auth.py      # Token extraction & validation
│   │   └── backend.py   # Capability API client
│   ├── models/          # Tool schemas (Pydantic)
│   └── lib/             # Utilities
│       ├── logging.py   # PII-masking logger
│       └── errors.py    # Error mapping logic
tests/
├── integration/
│   └── mcp/             # MCP-specific integration tests
└── unit/
    └── mcp/             # MCP unit tests
```

**Structure Decision**: Single project structure within the `src/mcp` namespace to isolate the MCP adapter from the core Capability API while sharing the same repository.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |