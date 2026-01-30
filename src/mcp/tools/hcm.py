import logging
import uuid
from typing import Dict, Any, Optional
from src.mcp.adapters.backend import backend_client
from src.mcp.adapters.auth import extract_principal
from src.mcp.lib.errors import map_backend_error
from src.mcp.lib.logging import audit_logger

logger = logging.getLogger(__name__)

async def get_token_from_context(ctx: Any) -> Optional[str]:
    """
    Helper to extract bearer token from MCP context metadata.
    Expects context to have a way to access metadata/headers.
    """
    try:
        # This depends on the specific MCP client and how it passes headers.
        # Often it's in the 'request' or 'metadata' of the context.
        # For now, we'll look for 'authorization' or 'Authorization'.
        
        # FastMCP context varies, but usually we can get it from session or extra params.
        # If not directly available, we might need to pass it as a tool argument for now
        # but the spec says "metadata/headers".
        
        # Let's assume the token is passed in ctx.session.extra_metadata or similar.
        # If it's not there, we'll try to get it from a standard place.
        metadata = getattr(ctx, "session", {}).get("metadata", {})
        token = metadata.get("authorization") or metadata.get("Authorization")
        
        if token and token.startswith("Bearer "):
            return token[7:]
        return token
    except:
        return None

async def get_employee(ctx: Any, employee_id: str) -> str:
    """Look up employee profile with role-based filtering (Passthrough to Capability API)."""
    token = await get_token_from_context(ctx)
    if not token:
        return "ERROR: Missing Authorization token in context."
    
    principal = extract_principal(token)
    principal_id = principal.subject if principal else "unknown"
    
    try:
        response = await backend_client.call_action(
            domain="workday.hcm",
            action="get_employee",
            parameters={"employee_id": employee_id},
            token=token
        )
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        error_msg = map_backend_error(e)
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id, status="error")
        return f"ERROR: {error_msg}"

async def get_manager_chain(ctx: Any, employee_id: str) -> str:
    """Get the reporting line for an employee."""
    token = await get_token_from_context(ctx)
    if not token:
        return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    principal_id = principal.subject if principal else "unknown"

    try:
        response = await backend_client.call_action(
            domain="workday.hcm",
            action="get_manager_chain",
            parameters={"employee_id": employee_id},
            token=token
        )
        audit_logger.log("get_manager_chain", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def get_org_chart(ctx: Any, root_id: str, depth: int = 2) -> str:
    """View the organizational structure starting from a root employee."""
    token = await get_token_from_context(ctx)
    if not token:
        return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    principal_id = principal.subject if principal else "unknown"

    try:
        response = await backend_client.call_action(
            domain="workday.hcm",
            action="get_org_chart",
            parameters={"root_id": root_id, "depth": depth},
            token=token
        )
        audit_logger.log("get_org_chart", {"root_id": root_id, "depth": depth}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def update_contact_info(ctx: Any, employee_id: str, updates: dict) -> str:
    """Update employee contact information (Personal Email, Phone). Enabled for AGENTS (No MFA)."""
    token = await get_token_from_context(ctx)
    if not token:
        return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    principal_id = principal.subject if principal else "unknown"

    try:
        response = await backend_client.call_action(
            domain="workday.hcm",
            action="update_contact_info",
            parameters={"employee_id": employee_id, "updates": updates},
            token=token
        )
        audit_logger.log("update_contact_info", {"employee_id": employee_id, "updates": updates}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def list_direct_reports(ctx: Any, manager_id: str) -> str:
    """View all direct reports for a given manager."""
    token = await get_token_from_context(ctx)
    if not token: return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    principal_id = principal.subject if principal else "unknown"

    try:
        response = await backend_client.call_action(
            domain="workday.hcm",
            action="list_direct_reports",
            parameters={"manager_id": manager_id},
            token=token
        )
        audit_logger.log("list_direct_reports", {"manager_id": manager_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"
