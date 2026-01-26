import os
from fastapi import APIRouter, Depends, HTTPException, Request
from src.domain.services.flow_service import FlowService
from src.domain.entities.flow import FlowStartRequest, FlowStatusResponse
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.flow_runner import FlowRunnerPort
from src.api.dependencies import get_current_principal, get_policy_engine, get_flow_runner_adapter
from src.adapters.auth import VerifiedPrincipal
from src.domain.entities.error import ErrorResponse

router = APIRouter(prefix="/flows", tags=["flows"])

def get_flow_service(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    adapter: FlowRunnerPort = Depends(get_flow_runner_adapter)
) -> FlowService:
    return FlowService(policy_engine, adapter)

@router.post(
    "/{domain}/{flow}",
    status_code=202,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def start_flow(
    domain: str,
    flow: str,
    request: FlowStartRequest,
    req: Request,
    service: FlowService = Depends(get_flow_service),
    principal: VerifiedPrincipal = Depends(get_current_principal)
):
    try:
        environment = os.getenv("ENVIRONMENT", "local")
        request_ip = req.client.host if req.client else None
        
        flow_id = await service.start_flow(
            domain=domain,
            flow=flow,
            params=request.parameters,
            principal_id=principal.subject,
            principal_groups=principal.groups,
            principal_type=principal.principal_type.value,
            environment=environment,
            mfa_verified=principal.mfa_verified,
            token_issued_at=principal.issued_at,
            token_expires_at=principal.expires_at,
            request_ip=request_ip
        )
        return {"flow_id": flow_id, "status": "RUNNING"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{flow_id}", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: str,
    service: FlowService = Depends(get_flow_service),
    principal: VerifiedPrincipal = Depends(get_current_principal)
):
    try:
        return await service.get_status(flow_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Flow not found")