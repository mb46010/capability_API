from src.mcp.adapters.auth import extract_principal, PrincipalContext

# ...

async def is_tool_allowed(ctx: Context, tool_name: str) -> bool:
    """
    Check if a tool is allowed for the current principal.
    Used for both dynamic discovery and execution enforcement.
    """
    token = await hcm.get_token_from_context(ctx)
    if not token: return False
    
    principal = extract_principal(token)
    if not principal: return False
    
    role = principal.principal_type
    
    # RBAC Mapping (FR-004)
    allowed_tools = {
        "AI_AGENT": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance"],
        "EMPLOYEE": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance", "request_time_off", "cancel_time_off", "list_pay_statements"],
        "ADMIN": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance", "request_time_off", "cancel_time_off", "list_pay_statements", "approve_time_off", "list_direct_reports", "get_compensation", "get_pay_statement"]
    }
    
    return tool_name in allowed_tools.get(role, [])

# Note: In a real implementation with FastMCP 3.0, we would use the 
# server's discovery hooks to filter the tool list returned to the client.

# --- Time Tools ---

# ... (Time tool registrations)

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
