from fastapi import FastAPI
import uvicorn
import os
from src.api.routes import actions, flows

app = FastAPI(
    title="HR AI Platform Capability API",
    description="Governed API exposing deterministic actions and long-running HR flows.",
    version="1.0.0"
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
