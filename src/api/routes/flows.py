from fastapi import APIRouter, Depends, HTTPException, Header
from src.domain.services.flow_runner import FlowRunner
from src.domain.entities.flow import FlowStartRequest, FlowStatusResponse
from src.adapters.filesystem.local_flow_runner import LocalFlowRunnerAdapter
from src.api.dependencies import get_current_principal

# Dependency injection setup
# Reuse PolicyEngine logic if flows are also governed by policy (Task description implies "Goal: Trigger and track... using local runner",
# but US2 integrated Policy. It's safer to add Policy Check here too, or at least a placeholder).

router = APIRouter(prefix="/flows", tags=["flows"])

# Singleton for MVP
_flow_runner = None

def get_flow_runner():
    global _flow_runner
    if not _flow_runner:
        adapter = LocalFlowRunnerAdapter()
        _flow_runner = FlowRunner(adapter)
    return _flow_runner

@router.post("/{domain}/{flow}", status_code=202)
async def start_flow(
    domain: str,
    flow: str,
    request: FlowStartRequest,
    runner: FlowRunner = Depends(get_flow_runner),
    principal: dict = Depends(get_current_principal)
):
    try:
        # TODO: Add Policy Check here similar to Action Service
        flow_id = await runner.start_flow(domain, flow, request.parameters)
        return {"flow_id": flow_id, "status": "RUNNING"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{flow_id}", response_model=FlowStatusResponse)
async def get_flow_status(
    flow_id: str,
    runner: FlowRunner = Depends(get_flow_runner),
    principal: dict = Depends(get_current_principal)
):
    try:
        return await runner.get_status(flow_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Flow not found")
