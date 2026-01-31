from typing import Optional, List, Any
from pydantic import BaseModel
import jwt
import logging

logger = logging.getLogger(__name__)

class PrincipalContext(BaseModel):
    subject: str
    principal_type: str
    groups: List[str] = []
    mfa_verified: bool = False
    raw_token: str

def extract_principal(token: str) -> Optional[PrincipalContext]:
    try:
        # Decode without verification - backend will verify. 
        # We just need the claims for tool discovery logic.
        payload = jwt.decode(token, options={"verify_signature": False})
        
        amr = payload.get("amr", [])
        mfa_verified = "mfa" in amr
        
        return PrincipalContext(
            subject=payload.get("sub", "unknown"),
            principal_type=payload.get("principal_type", "HUMAN"),
            groups=payload.get("groups", []),
            mfa_verified=mfa_verified,
            raw_token=token
        )
    except Exception as e:
        logger.error(f"Failed to decode token: {str(e)}")
        return None

def get_token_from_context(ctx: Any) -> Optional[str]:
    """
    Robustly extract bearer token from MCP context metadata.
    """
    try:
        # Check session metadata first (standard FastMCP pattern)
        session = getattr(ctx, "session", None)
        metadata = {}
        if isinstance(session, dict):
            metadata = session.get("metadata", {})
        elif session:
            metadata = getattr(session, "metadata", {})

        token = metadata.get("authorization") or metadata.get("Authorization")
        
        # Fallback to request headers if available (depends on transport)
        if not token:
            request = getattr(ctx, "request", None)
            if request:
                headers = getattr(request, "headers", {})
                token = headers.get("authorization") or headers.get("Authorization")

        if token and isinstance(token, str) and token.startswith("Bearer "):
            return token[7:]
        return token
    except Exception as e:
        logger.debug(f"Token extraction failed: {str(e)}")
        return None

def is_tool_allowed(principal: PrincipalContext, tool_name: str) -> bool:
    """
    Enforce RBAC mapping (FR-004).
    Resolves role from groups for HUMAN types.
    """
    # 1. Resolve Effective Role
    role = principal.principal_type
    if role == "HUMAN":
        if "hr-platform-admins" in principal.groups:
            role = "ADMIN"
        elif "employees" in principal.groups:
            role = "EMPLOYEE"
    
    # 2. Check Permissions
    allowed_tools = {
        "AI_AGENT": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance"],
        "EMPLOYEE": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance", "request_time_off", "cancel_time_off", "list_pay_statements"],
        "ADMIN": ["get_employee", "get_manager_chain", "get_org_chart", "update_contact_info", "get_pto_balance", "request_time_off", "cancel_time_off", "list_pay_statements", "approve_time_off", "list_direct_reports", "get_compensation", "get_pay_statement"]
    }
    
    is_allowed = tool_name in allowed_tools.get(role, [])
    
    if not is_allowed:
        logger.warning(f"Access Denied: principal={principal.subject}, type={principal.principal_type}, groups={principal.groups}, role={role}, tool={tool_name}")
    else:
        logger.debug(f"Access Granted: principal={principal.subject}, role={role}, tool={tool_name}")
        
    return is_allowed

async def authenticate_and_authorize(ctx: Any, tool_name: str) -> tuple[Optional[str], Optional[PrincipalContext], Optional[str]]:
    """
    Centralized auth and RBAC check for all tools.
    Returns (token, principal, error_message)
    """
    token = get_token_from_context(ctx)
    if not token:
        return None, None, "UNAUTHORIZED: Missing Authorization token in context."
    
    principal = extract_principal(token)
    if not principal:
        return None, None, "UNAUTHORIZED: Invalid or malformed token."
    
    if not is_tool_allowed(principal, tool_name):
        return None, None, f"FORBIDDEN: Principal type '{principal.principal_type}' is not authorized to use tool '{tool_name}'."
    
    return token, principal, None
