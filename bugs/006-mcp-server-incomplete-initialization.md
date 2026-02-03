# BUG-006: MCP Server Incomplete Initialization

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/mcp/server.py`
- **Line(s)**: 8

## Issue Description
The MCP server file contains a comment `# ... (init code)` suggesting incomplete or truncated initialization code:

```python
from src.mcp.adapters.auth import get_token_from_context, extract_principal, is_tool_allowed

# ... (init code)  # ❌ INCOMPLETE - Missing actual initialization

@mcp.resource("mcp://tools/list")
@mcp.tool()
async def list_available_tools(ctx: Context) -> str:
```

The `mcp` object is referenced but its initialization is not shown, suggesting either:
1. The file was truncated during review
2. Critical initialization code is missing
3. There's a separate import that creates `mcp`

If `mcp` is not properly initialized, the server will fail to start.

## Impact
- **Server failure**: If `mcp` is undefined, the server will crash on startup
- **Missing functionality**: Potentially missing auth middleware or configuration
- **Maintenance confusion**: Unclear initialization sequence

## Root Cause
The code appears to have been truncated or the initialization was moved/removed without updating the file structure. This may have occurred during a refactoring or code review process.

## How to Fix

### Code Changes
Ensure proper MCP server initialization:

```python
# ✅ FIXED - Complete initialization
from fastmcp import FastMCP, Context
from src.mcp.lib.logging import setup_logging
from src.mcp.lib.config import settings
from src.mcp.tools import hcm, time, payroll, discovery
from src.mcp.adapters.auth import get_token_from_context, extract_principal, is_tool_allowed

# Initialize logging
setup_logging()

# Create MCP server instance
mcp = FastMCP(
    name="hr-ai-capability-server",
    version="1.0.0",
    description="HR AI Platform MCP Server"
)

# Add middleware or hooks as needed
# mcp.add_middleware(auth_middleware)

@mcp.resource("mcp://tools/list")
@mcp.tool()
async def list_available_tools(ctx: Context) -> str:
    # ... rest of code
```

### Steps
1. Review `src/mcp/server.py` for the complete file content
2. Verify the `mcp` variable is properly initialized
3. Remove placeholder comments like `# ... (init code)`
4. Ensure all required middleware and configuration is present
5. Test MCP server startup

## Verification

### Test Cases
1. Run `python -m src.mcp.server` - should start without errors
2. Connect an MCP client and list tools
3. Execute a simple tool call

### Verification Steps
1. Start the MCP server standalone
2. Verify logs show proper initialization
3. Run MCP integration tests

## Related Issues
- None

---
*Discovered: 2026-02-03*
