import logging
import uuid
from typing import Dict, Any, Optional
from src.mcp.adapters.backend import backend_client
from src.mcp.adapters.auth import authenticate_and_authorize, get_mcp_token
from src.mcp.lib.errors import map_backend_error
from src.mcp.lib.logging import audit_logger

logger = logging.getLogger(__name__)

async def get_pto_balance(ctx: Any, employee_id: str) -> str:
    """Check vacation and sick leave balances."""
    user_token, principal, error = await authenticate_and_authorize(ctx, "get_pto_balance")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        mcp_token = await get_mcp_token(user_token)
        
        response = await backend_client.call_action(
            domain="workday.time",
            action="get_balance",
            parameters={"employee_id": employee_id},
            token=mcp_token
        )
        audit_logger.log("get_balance", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def request_time_off(ctx: Any, employee_id: str, type: str, start_date: str, end_date: str, hours: float, transaction_id: Optional[str] = None) -> str:
    """Submit a new time off request. Auto-generates transaction ID if not provided."""
    user_token, principal, error = await authenticate_and_authorize(ctx, "request_time_off")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject
    
    # Auto-generate Transaction ID for idempotency (Spec requirement)
    if not transaction_id:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"

    params = {
        "employee_id": employee_id,
        "type": type,
        "start_date": start_date,
        "end_date": end_date,
        "hours": hours,
        "transaction_id": transaction_id
    }

    try:
        mcp_token = await get_mcp_token(user_token)
        
        response = await backend_client.call_action(
            domain="workday.time",
            action="request",
            parameters=params,
            token=mcp_token
        )
        audit_logger.log("request_time_off", params, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def cancel_time_off(ctx: Any, request_id: str, reason: Optional[str] = None) -> str:
    """Cancel a pending or approved time off request."""
    user_token, principal, error = await authenticate_and_authorize(ctx, "cancel_time_off")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        mcp_token = await get_mcp_token(user_token)
        
        response = await backend_client.call_action(
            domain="workday.time",
            action="cancel",
            parameters={"request_id": request_id, "reason": reason},
            token=mcp_token
        )
        audit_logger.log("cancel_time_off", {"request_id": request_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"

async def approve_time_off(ctx: Any, request_id: str) -> str:
    """Approve a pending time off request (Manager-only)."""
    user_token, principal, error = await authenticate_and_authorize(ctx, "approve_time_off")
    if error: return f"ERROR: {error}"
    
    principal_id = principal.subject

    try:
        mcp_token = await get_mcp_token(user_token)
        
        response = await backend_client.call_action(
            domain="workday.time",
            action="approve",
            parameters={"request_id": request_id},
            token=mcp_token
        )
        audit_logger.log("approve_time_off", {"request_id": request_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        return f"ERROR: {map_backend_error(e)}"