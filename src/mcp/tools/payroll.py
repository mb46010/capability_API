import logging
from typing import Dict, Any, Optional
from src.mcp.adapters.backend import backend_client
from src.mcp.adapters.auth import extract_principal
from src.mcp.lib.errors import map_backend_error
from src.mcp.lib.logging import audit_logger

logger = logging.getLogger(__name__)

async def get_token_from_context(ctx: Any) -> Optional[str]:
    try:
        metadata = getattr(ctx, "session", {}).get("metadata", {})
        token = metadata.get("authorization") or metadata.get("Authorization")
        if token and token.startswith("Bearer "):
            return token[7:]
        return token
    except:
        return None

async def get_compensation(ctx: Any, employee_id: str) -> str:
    """View sensitive salary and bonus details. REQUIRES MFA."""
    token = await get_token_from_context(ctx)
    if not token: return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    if not principal: return "ERROR: Invalid token."
    
    # MFA Enforcement (Spec FR-005)
    if not principal.mfa_verified and principal.principal_type != "MACHINE":
        return "ERROR: MFA_REQUIRED: This action requires multi-factor authentication."

    try:
        response = await backend_client.call_action(
            domain="workday.payroll",
            action="get_compensation",
            parameters={"employee_id": employee_id},
            token=token
        )
        audit_logger.log("get_compensation", {"employee_id": employee_id}, principal.subject)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def get_pay_statement(ctx: Any, statement_id: str) -> str:
    """View detailed pay statement (stub/slip). REQUIRES MFA."""
    token = await get_token_from_context(ctx)
    if not token: return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    if not principal: return "ERROR: Invalid token."
    
    # MFA Enforcement
    if not principal.mfa_verified and principal.principal_type != "MACHINE":
        return "ERROR: MFA_REQUIRED: This action requires multi-factor authentication."

    try:
        response = await backend_client.call_action(
            domain="workday.payroll",
            action="get_pay_statement",
            parameters={"statement_id": statement_id},
            token=token
        )
        audit_logger.log("get_pay_statement", {"statement_id": statement_id}, principal.subject)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def list_pay_statements(ctx: Any, employee_id: str, year: Optional[int] = None) -> str:
    """List historical pay statements. REQUIRES MFA."""
    token = await get_token_from_context(ctx)
    if not token: return "ERROR: Missing Authorization token."
    
    principal = extract_principal(token)
    if not principal: return "ERROR: Invalid token."
    
    if not principal.mfa_verified and principal.principal_type != "MACHINE":
        return "ERROR: MFA_REQUIRED: This action requires multi-factor authentication."

    try:
        response = await backend_client.call_action(
            domain="workday.payroll",
            action="list_pay_statements",
            parameters={"employee_id": employee_id, "year": year},
            token=token
        )
        audit_logger.log("list_pay_statements", {"employee_id": employee_id, "year": year}, principal.subject)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"
