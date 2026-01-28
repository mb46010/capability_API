# Quickstart: HR Platform MCP Server

## Prerequisites
- Python 3.11+
- FastMCP 3.0 (`mcp[fastmcp]`)
- Running instance of Capability API (Port 8000)
- Running instance of Mock Okta (Port 9000)

## Installation

1. **Clone and Setup**:
   ```bash
   git checkout 005-hr-mcp-server
   pip install "mcp[fastmcp]" httpx pydantic-settings
   ```

2. **Environment Configuration**:
   Create a `.env` file in the root:
   ```env
   CAPABILITY_API_URL=http://localhost:8000
   MOCK_OKTA_URL=http://localhost:9000
   LOG_LEVEL=INFO
   ```

## Running the Server

Start the MCP server using the FastMCP CLI or directly with Python:

```bash
python src/mcp_server.py
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_mcp_tools.py
```

### Manual Verification (using MCP Inspector)
```bash
npx @modelcontextprotocol/inspector python src/mcp_server.py
```

## Integration with Chainlit
The Chainlit app should be configured to connect to `http://localhost:3000` (or the configured host/port) and pass the `auth_token` in the request context.

```
