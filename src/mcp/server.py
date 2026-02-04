import json
from fastmcp import FastMCP, Context
from src.mcp.lib.logging import setup_logging
from src.mcp.lib.config import settings
from src.mcp.tools import hcm, time, payroll, discovery
from src.mcp.adapters.auth import get_token_from_context, extract_principal, is_tool_allowed

# Initialize FastMCP server
mcp = FastMCP("hr-mcp-server")
setup_logging()

@mcp.resource("mcp://tools/list")
@mcp.tool()
async def list_available_tools(ctx: Context) -> str:
    """
    Dynamically lists all tools the current principal is authorized to use.
    Useful for discovery and UI filtering.
    """
    return await discovery.list_available_tools(ctx)

# --- HCM Tools ---

@mcp.tool()
async def get_employee(ctx: Context, employee_id: str) -> str:
    """Look up employee profile with role-based filtering (Passthrough to Capability API)."""
    return await hcm.get_employee(ctx, employee_id)

@mcp.tool()
async def get_manager_chain(ctx: Context, employee_id: str) -> str:
    """Get the reporting line for an employee."""
    return await hcm.get_manager_chain(ctx, employee_id)

@mcp.tool()
async def get_org_chart(ctx: Context, root_id: str, depth: int = 2) -> str:
    """View the organizational structure starting from a root employee."""
    return await hcm.get_org_chart(ctx, root_id, depth)

@mcp.tool()
async def list_direct_reports(ctx: Context, manager_id: str) -> str:
    """View all direct reports for a given manager."""
    return await hcm.list_direct_reports(ctx, manager_id)

@mcp.tool()
async def update_contact_info(ctx: Context, employee_id: str, updates: dict, transaction_id: str = None) -> str:
    """Update employee contact information (Personal Email, Phone). Enabled for AGENTS (No MFA)."""
    return await hcm.update_contact_info(ctx, employee_id, updates, transaction_id)

# --- Time Tools ---

@mcp.tool()
async def get_pto_balance(ctx: Context, employee_id: str) -> str:
    """Check vacation and sick leave balances."""
    return await time.get_pto_balance(ctx, employee_id)

@mcp.tool()
async def request_time_off(ctx: Context, employee_id: str, type: str, start_date: str, end_date: str, hours: float, transaction_id: str = None) -> str:
    """Submit a new time off request. Auto-generates transaction ID if not provided."""
    return await time.request_time_off(ctx, employee_id, type, start_date, end_date, hours, transaction_id)

@mcp.tool()
async def cancel_time_off(ctx: Context, request_id: str, reason: str = None) -> str:
    """Cancel a pending or approved time off request."""
    return await time.cancel_time_off(ctx, request_id, reason)

@mcp.tool()
async def approve_time_off(ctx: Context, request_id: str) -> str:
    """Approve a pending time off request (Manager-only)."""
    return await time.approve_time_off(ctx, request_id)

# --- Payroll Tools ---

@mcp.tool()
async def get_compensation(ctx: Context, employee_id: str) -> str:
    """View sensitive salary and bonus details. REQUIRES MFA."""
    return await payroll.get_compensation(ctx, employee_id)

@mcp.tool()
async def get_pay_statement(ctx: Context, statement_id: str) -> str:
    """View detailed pay statement. REQUIRES MFA."""
    return await payroll.get_pay_statement(ctx, statement_id)

@mcp.tool()
async def list_pay_statements(ctx: Context, employee_id: str, year: int = None) -> str:
    """List historical pay statements. REQUIRES MFA."""
    return await payroll.list_pay_statements(ctx, employee_id, year)

if __name__ == "__main__":
    mcp.run()
