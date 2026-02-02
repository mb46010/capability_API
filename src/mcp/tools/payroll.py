import logging
from typing import Optional
from src.mcp.lib.decorators import mcp_tool

logger = logging.getLogger(__name__)

@mcp_tool(domain="workday.payroll", action="get_compensation", require_mfa=True)
def get_compensation(employee_id: str) -> dict:
    """View sensitive salary and bonus details. REQUIRES MFA."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.payroll", action="get_pay_statement", require_mfa=True)
def get_pay_statement(statement_id: str) -> dict:
    """View detailed pay statement (stub/slip). REQUIRES MFA."""
    return {"statement_id": statement_id}

@mcp_tool(domain="workday.payroll", action="list_pay_statements", require_mfa=True)
def list_pay_statements(employee_id: str, year: Optional[int] = None) -> dict:
    """List historical pay statements. REQUIRES MFA."""
    return {"employee_id": employee_id, "year": year}
