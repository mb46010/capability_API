from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
from src.api.routes import actions, flows
from src.domain.entities.error import ErrorResponse

from src.adapters.workday.exceptions import WorkdayError

app = FastAPI(
    title="HR AI Platform Capability API",
    description="Governed API exposing deterministic actions and long-running HR flows.",
    version="1.0.0"
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    # Map HTTP status codes to semantic error codes
    status_to_code = {
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        424: "DEPENDENCY_FAILED",
        504: "GATEWAY_TIMEOUT"
    }
    
    error_code = status_to_code.get(exc.status_code, str(exc.status_code))
    
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=error_code,
            message=exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            details={"status_code": exc.status_code}
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
        "ALREADY_PROCESSED": 409,
        "CONNECTOR_TIMEOUT": 504,
        "CONNECTOR_UNAVAILABLE": 503,
        "RATE_LIMITED": 429
    }
    
    status_code = status_map.get(exc.error_code, 500)
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "retry_allowed": exc.retry_allowed
        }
    )

app.include_router(actions.router)
app.include_router(flows.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": os.getenv("ENVIRONMENT", "unknown")}

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )