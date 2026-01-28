# Research: HR Platform MCP Server Integration

## Decisions

### Framework: FastMCP 3.0 (Python)
- **Decision**: Use the Python-based FastMCP 3.0 framework for implementing the MCP server.
- **Rationale**: Aligns with Article I of the Constitution (Python-Native logic). FastMCP provides a high-level decorator-based API that simplifies tool definition and context management.
- **Alternatives considered**: MCP SDK (lower level), Node.js MCP (rejected due to constitutional Python preference).

### Authentication: Bearer Token Passthrough
- **Decision**: The MCP server will be stateless. It will extract the Bearer token from the incoming MCP request context (sent by Chainlit) and inject it into the headers of outbound calls to the Capability API.
- **Rationale**: Maintains Article II (Hexagonal Integrity) by treating the MCP server as a protocol adapter. It ensures the Capability API remains the single source of truth for policy enforcement.

### Tool Discovery: Dynamic Filtering
- **Decision**: Implement the `list_tools` MCP primitive to dynamically filter available tools based on the roles/claims found in the provided token.
- **Rationale**: Prevents AI model "hallucination" attempts on unauthorized tools (FR-004) and improves UX by only surfacing relevant actions.

### Logging & Privacy: PII Masking
- **Decision**: Implement a custom logging formatter or wrapper that redacts fields matching the PII schema (names, emails, phones, salaries) for standard logs, while allowing VERBOSE logging only to the protected audit trail.
- **Regulated by**: Article VIII (Professional Logging & Privacy).

## Best Practices for FastMCP 3.0

1. **Context Management**: Use the `Context` object to access request-level metadata (auth tokens).
2. **Metadata Tags**: Use the `tags` parameter in `@mcp.tool` to group tools by domain (hcm, payroll, time) as specified in FR-009.
3. **Async Everything**: All tool implementations must be `async` to handle I/O to the Capability API efficiently.
4. **Structured Errors**: Map backend error codes (MFA_REQUIRED, FORBIDDEN) to user-friendly MCP error responses.

## Integration Patterns

- **Pattern**: Protocol Adapter.
- **Flow**: Chainlit (Client) -> MCP (Protocol) -> FastMCP Server (Adapter) -> Capability API (Core Logic) -> Workday Simulator (Persistence).
