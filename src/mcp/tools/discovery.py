import json
from typing import Any
from src.mcp.adapters.auth import get_token_from_context, extract_principal, is_tool_allowed

async def list_available_tools(ctx: Any) -> str:
    """
    Dynamically lists all tools the current principal is authorized to use.
    Useful for discovery and UI filtering.
    """
    token = get_token_from_context(ctx)
    if not token:
        return json.dumps({"error": "Missing Authorization", "tools": []})
    
    principal = extract_principal(token)
    if not principal:
        return json.dumps({"error": "Invalid token", "tools": []})

    all_tools = [
        "get_employee", "get_manager_chain", "get_org_chart", "list_direct_reports", "update_contact_info",
        "get_pto_balance", "request_time_off", "cancel_time_off", "approve_time_off",
        "get_compensation", "get_pay_statement", "list_pay_statements"
    ]
    
    allowed = [t for t in all_tools if is_tool_allowed(principal, t)]
    
    return json.dumps({
        "principal": principal.subject,
        "role": principal.principal_type,
        "available_tools": allowed
    })
