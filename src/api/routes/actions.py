import os
from fastapi import APIRouter, Depends, Header
from src.domain.services.action_service import ActionService
from src.domain.entities.action import ActionRequest, ActionResponse
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.connectors.mock_connector import MockConnectorAdapter
from src.api.dependencies import get_current_principal

router = APIRouter(prefix="/actions", tags=["actions"])

# Simple dependency injection setup (Singleton-ish for this MVP)
POLICY_PATH = os.getenv("POLICY_PATH", "config/policy.yaml")
_policy_engine = None
_connector = MockConnectorAdapter()

def get_action_service():
    global _policy_engine
    if not _policy_engine:
        # Load policy once
        loader = FilePolicyLoaderAdapter(POLICY_PATH)
        policy = loader.load_policy()
        _policy_engine = PolicyEngine(policy)
    
    return ActionService(_policy_engine, _connector)

@router.post("/{domain}/{action}", response_model=ActionResponse)
async def execute_action(
    domain: str,
    action: str,
    request: ActionRequest,
    service: ActionService = Depends(get_action_service),
    principal: dict = Depends(get_current_principal)
):
    environment = os.getenv("ENVIRONMENT", "local")
    
    return await service.execute_action(
        domain=domain,
        action=action,
        parameters=request.parameters,
        principal_id=principal["id"],
        principal_groups=principal["groups"],
        principal_type=principal["type"],
        environment=environment
    )
