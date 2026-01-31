from typing import Optional, List, Any, Dict, Tuple
from pydantic import BaseModel
import jwt
import logging
import time
import httpx
from src.mcp.lib.config import settings

logger = logging.getLogger(__name__)

# Token Cache: Key = user_token_signature, Value = (mcp_token, expires_at_timestamp)
_mcp_token_cache: Dict[str, Tuple[str, float]] = {}

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

async def get_mcp_token(user_token: str) -> str:
    """
    Exchange user token for MCP-scoped token with caching.
    
    Args:
        user_token: The full user token.
        
    Returns:
        The MCP-scoped token.
        
    Raises:
        Exception: If exchange fails.
    """
    # 1. Check Cache
    # We use the token signature (last part) as key to save memory/log-safety
    token_parts = user_token.split(".")
    cache_key = token_parts[-1] if len(token_parts) == 3 else user_token
    
    now = time.time()
    if cache_key in _mcp_token_cache:
        cached_token, expires_at = _mcp_token_cache[cache_key]
        if now < expires_at:
            logger.debug("Returning cached MCP token")
            return cached_token
        else:
            del _mcp_token_cache[cache_key]

    # 2. Perform Exchange
    logger.info("Exchanging user token for MCP scope")
    token_endpoint = f"{settings.OKTA_ISSUER}/v1/token"
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            token_endpoint,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
                "subject_token": user_token,
                "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
                "scope": "mcp:use",
                "audience": settings.CAPABILITY_API_AUDIENCE
            }
        )
        response.raise_for_status()
        data = response.json()
        
    mcp_token = data["access_token"]
    
    # 3. Cache Result
    # Cache for 4 minutes (240s) to be safe within 5 min TTL
    expires_at = now + 240
    _mcp_token_cache[cache_key] = (mcp_token, expires_at)
    
    return mcp_token

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