from fastapi import FastAPI, Request, HTTPException
from typing import Union
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
from src.lib.context import set_request_id
from src.api.routes import actions, flows, audit
from src.domain.entities.error import ErrorResponse
from src.adapters.workday.exceptions import WorkdayError
from src.lib.config_validator import settings

app = FastAPI(
    title="HR AI Platform Capability API",
    description="Governed API exposing deterministic actions and long-running HR flows.",
    version="1.0.0"
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "geolocation=()"
    if settings.ENVIRONMENT != "local":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: Union[HTTPException, StarletteHTTPException]):
    # Map HTTP status codes to semantic error codes
    status_to_code = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        424: "DEPENDENCY_FAILED",
        500: "INTERNAL_SERVER_ERROR",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = status_to_code.get(exc.status_code, str(exc.status_code))
    
    # Sanitize message in production for server errors
    is_local = settings.ENVIRONMENT == "local"
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    if not is_local and exc.status_code >= 500:
        message = "An internal server error occurred."
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=message,
            details={"status_code": exc.status_code} if is_local else None
        ).model_dump(mode='json')
    )

@app.exception_handler(WorkdayError)
async def workday_error_handler(request: Request, exc: WorkdayError):
    # Map to appropriate HTTP status
    status_map = {
        "EMPLOYEE_NOT_FOUND": 404,
        "REQUEST_NOT_FOUND": 404,
        "STATEMENT_NOT_FOUND": 404,
        "INSUFFICIENT_BALANCE": 400,
        "INVALID_DATE_RANGE": 400,
        "INVALID_APPROVER": 403,
        "UNAUTHORIZED": 403,
        "MFA_REQUIRED": 401,
        "ALREADY_PROCESSED": 409,
        "CONNECTOR_TIMEOUT": 504,
        "CONNECTOR_UNAVAILABLE": 503,
        "RATE_LIMITED": 429
    }
    
    status_code = status_map.get(exc.error_code, 500)
    is_local = settings.ENVIRONMENT == "local"
    
    message = exc.message
    details = exc.details
    
    # Sanitize in production for server-side connector errors
    if not is_local and status_code >= 500:
        message = "A backend connector error occurred."
        details = None
    
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=message,
            details=details if is_local or status_code < 500 else None,
            retry_allowed=exc.retry_allowed
        ).model_dump(mode='json')
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all for unhandled exceptions to prevent leaking stack traces."""
    is_local = settings.ENVIRONMENT == "local"
    
    message = str(exc)
    if not is_local:
        message = "An unexpected error occurred."
        
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message=message
        ).model_dump(mode='json')
    )

app.include_router(actions.router)
app.include_router(flows.router)
app.include_router(audit.router)

# Mount demo reset endpoint if enabled
if os.getenv("ENABLE_DEMO_RESET", "false").lower() == "true":
    from src.api.routes import demo
    app.include_router(demo.router)

# Mount mock Okta provider routes in local environment for testing

if settings.ENVIRONMENT == "local":
    from src.adapters.auth import create_mock_okta_app
    from src.api.dependencies import provider
    mock_okta = create_mock_okta_app(provider)
    app.mount("/auth", mock_okta)

from fastapi import Depends
from src.domain.ports.connector import ConnectorPort
from src.domain.services.policy_engine import PolicyEngine
from src.api.dependencies import get_policy_engine, get_connector

# ... (previous code)

@app.get("/health")
async def health_check(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    connector: ConnectorPort = Depends(get_connector)
):
    """
    Health check endpoint verifying core dependencies.
    """
    health_status = {
        "status": "ok",
        "environment": settings.ENVIRONMENT,
        "dependencies": {
            "policy_engine": "unknown",
            "connector": "unknown"
        }
    }
    
    # 1. Verify Policy Engine
    try:
        # Simple check: verify policy object exists
        if policy_engine.policy:
            health_status["dependencies"]["policy_engine"] = "ok"
        else:
            health_status["dependencies"]["policy_engine"] = "failed"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["policy_engine"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    # 2. Verify Connector (Workday Simulator)
    try:
        # Simple check: verify it's initialized (we could add a ping method to interface later)
        if connector:
            health_status["dependencies"]["connector"] = "ok"
        else:
            health_status["dependencies"]["connector"] = "failed"
            health_status["status"] = "degraded"
    except Exception as e:
        health_status["dependencies"]["connector"] = f"error: {str(e)}"
        health_status["status"] = "degraded"

    if health_status["status"] != "ok":
        # Return 503 if critical dependencies are missing
        raise HTTPException(status_code=503, detail=health_status)

    return health_status

if __name__ == "__main__":
    is_development = settings.ENVIRONMENT in ["local", "dev"]

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development,
        workers=1 if is_development else 4,
        log_level="debug" if is_development else "info"
    )
