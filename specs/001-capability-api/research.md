# Research & Decisions: Capability API

**Status**: Complete
**Date**: 2026-01-26

## 1. Policy Engine Implementation
**Decision**: Custom Python Implementation
- **Rationale**: The provided `policy-schema.json` and `policy-schema.md` define a specific, deterministic evaluation logic (e.g., specific precedence rules, dot-notation wildcards). Using a general-purpose engine like OPA/Rego or Casbin would require mapping this custom logic into their DSLs, adding complexity and "non-Python" logic. A pure Python implementation using Pydantic for validation and standard string/regex for matching ensures full "Python-Native" compliance (Constitution Article I) and easier debugging.
- **Alternatives Considered**: 
    - **OPA (Open Policy Agent)**: Powerful but introduces a new language (Rego) and runtime dependency. Overkill for the specified schema.
    - **Casbin**: Good for ACL/RBAC, but the "Capabilities" + "Wildcard" + "Environment" model is specific enough that custom code is cleaner.

## 2. MCP (Model Context Protocol) Integration
**Decision**: Use `mcp` Python SDK as "Connector Adapters"
- **Rationale**: The spec treats MCP servers strictly as connectors. The Capability API acts as an MCP *Client*. We will wrap `mcp.ClientSession` in our hexagonal `adapters/connectors/` layer.
- **Pattern**: 
    - Each "Capability" (e.g., `workday.get_employee`) maps to an MCP Tool call.
    - The Adapter handles the connection (Stdio/SSE) and protocol details.

## 3. Local Workflow Simulation (Flows)
**Decision**: Simple Async State Machine (In-Memory)
- **Rationale**: For local development, we don't need a full Step Functions emulator (like LocalStack) if we just need to validate the *hand-off* and *callback* logic. A simple Service that tracks "Flow State" in a local JSON file and runs steps via `asyncio` is sufficient to prove the architecture.
- **Cloud Path**: This `FlowRunner` port will have an AWS adapter that simply calls `boto3.client('sfn').start_execution()`.

## 4. JSON with Provenance
**Decision**: Standard Envelope Format
- **Structure**:
    ```json
    {
      "data": { ... },
      "meta": {
        "provenance": {
          "source": "workday-connector-v1",
          "timestamp": "2026-01-26T10:00:00Z",
          "latency_ms": 120,
          "trace_id": "abc-123"
        }
      }
    }
    ```
- **Rationale**: Meets FR-001 requirements explicitly.

## 5. PII Masking
**Decision**: Middleware + Custom Formatter
- **Rationale**: To meet Constitution Article VIII, we cannot rely on developers remembering to mask. We will implement a `logging.Formatter` that runs regex replacements for common PII patterns (Emails, SSNs, Phones) before outputting.