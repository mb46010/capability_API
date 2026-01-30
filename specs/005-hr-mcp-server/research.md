# Research: HR Platform MCP Server

## FastMCP 3.0 Integration Patterns
- **Decision**: Use `FastMCP` class from `fastmcp` package for high-level tool definition.
- **Rationale**: Provides automatic schema generation and a clean decorator-based interface.
- **Alternatives considered**: `mcp` SDK (Too low-level, requires manual schema management).

## PII Masking with Standard Logging
- **Decision**: Implement a custom `logging.Filter` or `logging.Formatter` that uses regex patterns to redact sensitive fields (emails, phone numbers, SSNs) in JSON and text logs.
- **Rationale**: Compliance with Constitution Article VIII. Centralized masking ensures no accidental leaks.
- **Alternatives considered**: Individual redaction in every log call (Error-prone and violates DRY).

## Bearer Token Extraction and Passthrough
- **Decision**: Extract token from MCP session metadata/headers and pass it as an `Authorization` header in all backend calls via `httpx.AsyncClient`.
- **Rationale**: Statelessness and alignment with Capability API security architecture.
- **Alternatives considered**: Shared service account (Violates RBAC/Principal tracking).

## Local Service Discovery
- **Decision**: Use `pydantic-settings` to load `CAPABILITY_API_BASE_URL` from `.env`.
- **Rationale**: Flexibility for local development (pointing to localhost) vs containerized testing.
- **Alternatives considered**: Hardcoded URLs (Violates Constitution Article V).

## FastMCP RBAC (Dynamic Tool Discovery)
- **Decision**: Leverage `FastMCP`'s ability to filter tools during the `list_tools` request based on the caller's identity extracted from the session context.
- **Rationale**: Ensures AI Agents or restricted users cannot even "see" unauthorized tools.
- **Alternatives considered**: Server-side error on call (Poorer UX for AI Agents).