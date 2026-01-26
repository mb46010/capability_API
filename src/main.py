from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
import os
from src.api.routes import actions, flows
from src.domain.entities.error import ErrorResponse

app = FastAPI(
    title="HR AI Platform Capability API",
    description="Governed API exposing deterministic actions and long-running HR flows.",
    version="1.0.0"
)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error_code=str(exc.status_code), # Map status code to error code for now, or exc.detail if it's structured
            message=exc.detail if isinstance(exc.detail, str) else "An error occurred",
            details=exc.detail if isinstance(exc.detail, dict) else None
        ).model_dump()
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