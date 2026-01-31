import os
from typing import Optional
from fastapi import APIRouter, Depends, Request, Header
from src.domain.services.action_service import ActionService
from src.domain.entities.action import ActionRequest, ActionResponse
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.connector import ConnectorPort
from src.api.dependencies import get_current_principal, get_policy_engine, get_connector
from src.adapters.auth import VerifiedPrincipal
from src.domain.entities.error import ErrorResponse
from src.adapters.workday.client import WorkdaySimulator

router = APIRouter(prefix="/actions", tags=["actions"])

@router.post("/test/reload-fixtures")
async def reload_fixtures(connector: ConnectorPort = Depends(get_connector)):
    """Reload fixture data without restarting server."""
    if isinstance(connector, WorkdaySimulator):
        connector.reload()
        return {"status": "reloaded", "type": "workday"}
    return {"status": "ignored", "reason": "not using workday simulator"}

def get_action_service(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    connector: ConnectorPort = Depends(get_connector)
) -> ActionService:
    return ActionService(policy_engine, connector)

from fastapi import APIRouter, Depends, Request, Header
# ... (imports)
@router.post(
    "/{domain}/{action}",
    response_model=ActionResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        424: {"model": ErrorResponse}
    }
)
async def execute_action(
    domain: str,
    action: str,
    request: ActionRequest,
    req: Request,
    service: ActionService = Depends(get_action_service),
    principal: VerifiedPrincipal = Depends(get_current_principal),
    x_idempotency_key: Optional[str] = Header(None)
):
    environment = os.getenv("ENVIRONMENT", "local")
    request_ip = req.client.host if req.client else None
    
    return await service.execute_action(
        domain=domain,
        action=action,
        parameters=request.parameters,
        principal_id=principal.subject,
        principal_groups=principal.groups,
        principal_type=principal.principal_type.value,
        environment=environment,
        mfa_verified=principal.mfa_verified,
        token_issued_at=principal.issued_at,
        token_expires_at=principal.expires_at,
        request_ip=request_ip,
        idempotency_key=x_idempotency_key
    )
