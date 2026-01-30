# Quickstart: HR Platform MCP Server

## Development Setup

### 1. Prerequisites
- Python 3.11+
- Working Capability API instance (Local or Remote)

### 2. Environment Configuration
Create a `.env` file in the project root:
```bash
CAPABILITY_API_BASE_URL=http://localhost:8000
LOG_LEVEL=INFO
AUDIT_LOG_PATH=logs/mcp-audit.jsonl
```

### 3. Running the MCP Server
```bash
# Install dependencies
pip install fastmcp httpx pydantic-settings

# Start the server (Inspector mode recommended for dev)
fastmcp dev src/mcp/server.py
```

## Testing Tools

### Using the MCP Inspector
FastMCP provides a built-in inspector at `http://localhost:3000` when running in `dev` mode. Use it to:
- Browse available tools (Verify RBAC based on token).
- Execute tools with test parameters.
- Inspect raw MCP JSON-RPC traffic.

### Automated Tests
```bash
# Run all MCP tests
pytest tests/unit/mcp/ tests/integration/mcp/
```

## Security Note
All tools require a valid Bearer token passed via the client. For local testing, use the Capability API's mock token endpoint to generate valid tokens for different personas.