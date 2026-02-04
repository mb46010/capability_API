from fastapi import FastAPI, Request, HTTPException, Depends
from src.domain.ports.connector import ConnectorPort
from src.domain.services.policy_engine import PolicyEngine
from src.api.dependencies import get_policy_engine, get_connector

from typing import Union
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
import uuid
import asyncio
import logging
import time
from src.lib.context import set_request_id, get_request_id
from src.lib.logging import setup_logging
from src.api.routes import actions, flows, audit
from src.domain.entities.error import ErrorResponse
from src.adapters.workday.exceptions import WorkdayError
from src.lib.config_validator import settings
from src import __version__

# Initialize structured logging
log_level = logging.DEBUG if settings.ENVIRONMENT in ["local", "dev"] else logging.INFO
setup_logging(level=log_level)
request_logger = logging.getLogger("api.requests")

app = FastAPI(
    title="HR AI Platform Capability API",
    description="Governed API exposing deterministic actions and long-running HR flows.",
    version="1.0.0",
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()

    response = await call_next(request)

    latency_ms = (time.time() - start) * 1000

    # Extract principal if it was set in request.state
    principal_data = {}
    if hasattr(request.state, "principal"):
        p = request.state.principal
        principal_data = {
            "subject": p.subject,
            "principal_type": p.principal_type.value
            if hasattr(p.principal_type, "value")
            else str(p.principal_type),
            "groups": p.groups,
        }

    request_logger.info(
        f"{request.method} {request.url.path} {response.status_code}",
        extra={
            "extra_data": {
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "content_length": response.headers.get("content-length"),
                "principal": principal_data if principal_data else None,
            }
        },
    )

    return response


@app.middleware("http")
async def add_timeout(request: Request, call_next):
    try:
        return await asyncio.wait_for(
            call_next(request), timeout=settings.REQUEST_TIMEOUT_SECONDS
        )
    except asyncio.TimeoutError:
        return JSONResponse(
            status_code=504,
            content=ErrorResponse(
                error_code="GATEWAY_TIMEOUT",
                message="Request timed out",
                details={"timeout_seconds": settings.REQUEST_TIMEOUT_SECONDS},
            ).model_dump(mode="json"),
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
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response


@app.exception_handler(StarletteHTTPException)
@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: Union[HTTPException, StarletteHTTPException]
):
    # Map HTTP status codes to semantic error codes
    status_to_code = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        424: "DEPENDENCY_FAILED",
        500: "INTERNAL_SERVER_ERROR",
        504: "GATEWAY_TIMEOUT",
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
            details={"status_code": exc.status_code} if is_local else None,
        ).model_dump(mode="json"),
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
        "RATE_LIMITED": 429,
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
            retry_allowed=exc.retry_allowed,
        ).model_dump(mode="json"),
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
            error_code="INTERNAL_SERVER_ERROR", message=message
        ).model_dump(mode="json"),
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


@app.get("/health")
async def health_check(
    policy_engine: PolicyEngine = Depends(get_policy_engine),
    connector: ConnectorPort = Depends(get_connector),
):
    """
    Enhanced health check endpoint with detailed dependency probes.
    """
    start = time.time()
    health_status = {
        "status": "ok",
        "version": __version__,
        "environment": settings.ENVIRONMENT,
        "checks": {},
        "response_time_ms": 0,
    }

    # 1. Policy Engine Check
    pe_start = time.time()
    try:
        policy_count = len(policy_engine.policy.policies)
        health_status["checks"]["policy_engine"] = {
            "status": "ok",
            "policy_count": policy_count,
            "response_time_ms": round((time.time() - pe_start) * 1000, 2),
        }
    except Exception as e:
        health_status["checks"]["policy_engine"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    # 2. Connector Check (Workday Simulator)
    conn_start = time.time()
    try:
        # Check employee count as lightweight probe
        # Note: We use hasattr because the interface doesn't guarantee .employees
        employee_count = (
            len(connector.employees) if hasattr(connector, "employees") else 0
        )
        health_status["checks"]["connector"] = {
            "status": "ok",
            "type": type(connector).__name__,
            "employee_count": employee_count,
            "response_time_ms": round((time.time() - conn_start) * 1000, 2),
        }
    except Exception as e:
        health_status["checks"]["connector"] = {"status": "error", "error": str(e)}
        health_status["status"] = "degraded"

    health_status["response_time_ms"] = round((time.time() - start) * 1000, 2)

    if health_status["status"] != "ok":
        # Return 503 if any dependency is in error state
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
        log_level="debug" if is_development else "info",
    )
