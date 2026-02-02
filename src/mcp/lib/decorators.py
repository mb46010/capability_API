from functools import wraps
from typing import Any, Dict, Optional, Callable
import asyncio
import logging
from src.mcp.adapters.backend import backend_client
from src.mcp.adapters.auth import authenticate_and_authorize, get_mcp_token
from src.mcp.lib.errors import map_backend_error
from src.mcp.lib.logging import audit_logger

logger = logging.getLogger(__name__)

def mcp_tool(domain: str, action: str, tool_name: Optional[str] = None, require_mfa: bool = False):
    """
    Decorator that handles MCP tool boilerplate:
    1. Authentication & Authorization (RBAC)
    2. MFA Enforcement (optional)
    3. Token Exchange (User -> MCP)
    4. Backend Capability API Call
    5. Audit Logging
    6. Error Mapping
    """
    def decorator(func: Callable):
        # Default to function name if tool_name is not provided
        effective_tool_name = tool_name or func.__name__
        
        @wraps(func)
        async def wrapper(ctx: Any, *args, **kwargs) -> str:
            # 1. Auth & Authz
            # authenticate_and_authorize returns (token, principal, error)
            user_token, principal, error = await authenticate_and_authorize(ctx, effective_tool_name)
            if error:
                return f"ERROR: {error}"
            
            principal_id = principal.subject
            
            # 2. MFA Enforcement (FR-005)
            if require_mfa and not principal.mfa_verified and principal.principal_type != "MACHINE":
                return "ERROR: MFA_REQUIRED: This action requires multi-factor authentication."

            # 3. Parameter Preparation
            # The decorated function should return a dict of parameters for the backend call.
            parameters = {}
            try:
                if asyncio.iscoroutinefunction(func):
                    parameters = await func(*args, **kwargs)
                else:
                    parameters = func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Parameter preparation failed for {effective_tool_name}: {str(e)}")
                return f"ERROR: Parameter preparation failed: {str(e)}"

            try:
                # 4. Token Exchange
                mcp_token = await get_mcp_token(user_token)

                # 5. Backend Call
                response = await backend_client.call_action(
                    domain=domain,
                    action=action,
                    parameters=parameters,
                    token=mcp_token
                )

                # 6. Audit Success
                audit_logger.log(effective_tool_name, parameters, principal_id)
                return str(response.get("data", {}))

            except Exception as e:
                # 7. Audit Failure & Error Mapping
                error_msg = map_backend_error(e)
                audit_logger.log(effective_tool_name, parameters, principal_id, status="error")
                return f"ERROR: {error_msg}"

        return wrapper
    return decorator
