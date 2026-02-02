import logging
import uuid
from typing import Optional
from src.mcp.lib.decorators import mcp_tool

logger = logging.getLogger(__name__)

@mcp_tool(domain="workday.time", action="get_balance", tool_name="get_pto_balance")
def get_pto_balance(employee_id: str) -> dict:
    """Check vacation and sick leave balances."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.time", action="request", tool_name="request_time_off")
def request_time_off(employee_id: str, type: str, start_date: str, end_date: str, hours: float, transaction_id: Optional[str] = None) -> dict:
    """Submit a new time off request. Auto-generates transaction ID if not provided."""
    if not transaction_id:
        transaction_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    return {
        "employee_id": employee_id,
        "type": type,
        "start_date": start_date,
        "end_date": end_date,
        "hours": hours,
        "transaction_id": transaction_id
    }

@mcp_tool(domain="workday.time", action="cancel", tool_name="cancel_time_off")
def cancel_time_off(request_id: str, reason: Optional[str] = None) -> dict:
    """Cancel a pending or approved time off request."""
    return {"request_id": request_id, "reason": reason}

@mcp_tool(domain="workday.time", action="approve", tool_name="approve_time_off")
def approve_time_off(request_id: str) -> dict:
    """Approve a pending time off request (Manager-only)."""
    return {"request_id": request_id}
