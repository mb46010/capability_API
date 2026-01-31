# Developer Onboarding: HR MCP Server

Welcome! This guide will help you get the HR MCP Server running locally for development and testing.

## 1. Prerequisites
- **Python 3.11+**
- **Capability API**: Ensure the backend is running (usually on port 8000).
- **Mock Okta**: Ensure the mock OIDC provider is accessible (usually via the Capability API mount at `/auth`).

## 2. Environment Configuration
Create or update your `.env` file in the project root:

```bash
CAPABILITY_API_BASE_URL=http://localhost:8000
ENVIRONMENT=local
LOG_LEVEL=DEBUG
AUDIT_LOG_PATH=logs/mcp-audit.jsonl
```

## 3. Installation
Install the necessary dependencies:

```bash
pip install fastmcp mcp httpx PyJWT pydantic-settings
```

## 4. Running the Server

### Development Mode (with Inspector)
FastMCP includes a developer inspector that allows you to test tools in a web UI.

```bash
fastmcp dev src/mcp/server.py
```
- **Tools UI**: Open `http://localhost:3000` to browse and call tools.
- **Mock Token**: Use the Capability API's `/auth/test/tokens` endpoint to generate a token, then add it to the "Headers" or "Metadata" section in the inspector.

### Production Mode (Stdio)
For use with AI clients like Claude Desktop or a custom agent:

```bash
python -m src.mcp.server
```

## 5. Running Tests
We use `pytest` for all levels of testing.

```bash
# Unit tests
pytest tests/unit/mcp/

# Integration tests
pytest tests/integration/mcp/

# Performance (Latency) tests
pytest tests/performance/mcp/
```

## 6. Troubleshooting

### "ModuleNotFoundError: No module named 'mcp.types'"
Ensure both `fastmcp` and `mcp` are installed. Run:
`pip install fastmcp mcp`

### "ERROR: FORBIDDEN"
- Check that your token has the correct `principal_type` (HUMAN, AI_AGENT).
- If principal is HUMAN, ensure it belongs to the correct group (`hr-platform-admins` for ADMIN, `employees` for EMPLOYEE).
- Check `src/mcp/adapters/auth.py` for the RBAC mapping.

### "ERROR: MFA_REQUIRED"
Ensure your mock token contains the `amr: ["mfa"]` claim. You can generate this via the test token endpoint.
