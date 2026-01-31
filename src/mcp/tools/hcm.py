import logging
import uuid
from typing import Dict, Any, Optional
from src.mcp.adapters.backend import backend_client
from src.mcp.adapters.auth import authenticate_and_authorize
from src.mcp.lib.errors import map_backend_error
from src.mcp.lib.logging import audit_logger

logger = logging.getLogger(__name__)

async def get_employee(ctx: Any, employee_id: str) -> str:
    """Look up employee profile with role-based filtering (Passthrough to Capability API)."""
    token, principal, error = await authenticate_and_authorize(ctx, "get_employee")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject
    
    try:
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="get_employee",
            parameters={"employee_id": employee_id},
            token=token
        )
        response = await coro
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        error_msg = map_backend_error(e)
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id, status="error")
        return f"ERROR: {error_msg}"

async def get_manager_chain(ctx: Any, employee_id: str) -> str:
    """Get the reporting line for an employee."""
    token, principal, error = await authenticate_and_authorize(ctx, "get_manager_chain")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="get_manager_chain",
            parameters={"employee_id": employee_id},
            token=token
        )
        response = await coro
        audit_logger.log("get_manager_chain", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def get_org_chart(ctx: Any, root_id: str, depth: int = 2) -> str:
    """View the organizational structure starting from a root employee."""
    token, principal, error = await authenticate_and_authorize(ctx, "get_org_chart")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="get_org_chart",
            parameters={"root_id": root_id, "depth": depth},
            token=token
        )
        response = await coro
        audit_logger.log("get_org_chart", {"root_id": root_id, "depth": depth}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def update_contact_info(ctx: Any, employee_id: str, updates: dict) -> str:
    """Update employee contact information (Personal Email, Phone). Enabled for AGENTS (No MFA)."""
    token, principal, error = await authenticate_and_authorize(ctx, "update_contact_info")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="update_contact_info",
            parameters={"employee_id": employee_id, "updates": updates},
            token=token
        )
        response = await coro
        audit_logger.log("update_contact_info", {"employee_id": employee_id, "updates": updates}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def list_direct_reports(ctx: Any, manager_id: str) -> str:
    """View all direct reports for a given manager."""
    token, principal, error = await authenticate_and_authorize(ctx, "list_direct_reports")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="list_direct_reports",
            parameters={"manager_id": manager_id},
            token=token
        )
        response = await coro
        audit_logger.log("list_direct_reports", {"manager_id": manager_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"
