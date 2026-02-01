from fastapi import APIRouter
from src.api.dependencies import get_policy_engine, get_connector, get_flow_runner_adapter

router = APIRouter(prefix="/demo", tags=["demo"])

@router.post("/reset")
async def reset_services():
    """
    Clear lru_caches for core services to force re-initialization.
    Allows reloading policies and simulator state without restart.
    """
    get_policy_engine.cache_clear()
    get_connector.cache_clear()
    get_flow_runner_adapter.cache_clear()
    
    return {
        "status": "reset",
        "message": "Service caches cleared. Next request will re-initialize dependencies."
    }
