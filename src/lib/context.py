from contextvars import ContextVar
import uuid

# Context variable to store the request ID for the current task/request
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")

def get_request_id() -> str:
    """Get the current request ID or generate a new one if not set."""
    rid = request_id_ctx.get()
    if not rid:
        rid = str(uuid.uuid4())
        request_id_ctx.set(rid)
    return rid

def set_request_id(request_id: str) -> None:
    """Set the request ID for the current context."""
    request_id_ctx.set(request_id)
