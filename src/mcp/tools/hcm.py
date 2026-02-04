import logging
import uuid
from typing import Dict, Any, Optional
from src.mcp.lib.decorators import mcp_tool

logger = logging.getLogger(__name__)

@mcp_tool(domain="workday.hcm", action="get_employee")
def get_employee(employee_id: str) -> dict:
    """Look up employee profile with role-based filtering (Passthrough to Capability API)."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.hcm", action="get_manager_chain")
def get_manager_chain(employee_id: str) -> dict:
    """Get the reporting line for an employee."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.hcm", action="get_org_chart")
def get_org_chart(root_id: str, depth: int = 2) -> dict:
    """View the organizational structure starting from a root employee."""
    return {"root_id": root_id, "depth": depth}

@mcp_tool(domain="workday.hcm", action="update_contact_info")
def update_contact_info(employee_id: str, updates: dict, transaction_id: Optional[str] = None) -> dict:
    """Update employee contact information (Personal Email, Phone). Enabled for AGENTS (No MFA)."""
    if not transaction_id:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    return {"employee_id": employee_id, "updates": updates, "transaction_id": transaction_id}

@mcp_tool(domain="workday.hcm", action="list_direct_reports")
def list_direct_reports(manager_id: str) -> dict:
    """View all direct reports for a given manager."""
    return {"manager_id": manager_id}