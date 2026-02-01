from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_current_principal, get_policy_engine, get_connector, get_flow_runner_adapter
from src.adapters.auth import VerifiedPrincipal

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/reset")
async def reset_services(
    principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """
    Clear lru_caches for core services to force re-initialization.
    Allows reloading policies and simulator state without restart.
    Admin access required.
    """
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")

    get_policy_engine.cache_clear()
    get_connector.cache_clear()
    get_flow_runner_adapter.cache_clear()

    return {
        "status": "reset",
        "reset_by": principal.subject,
        "message": "Service caches cleared. Next request will re-initialize dependencies."
    }
