import json
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_current_principal
from src.adapters.auth import VerifiedPrincipal

router = APIRouter(prefix="/audit", tags=["audit"])

# Define default log path
DEFAULT_LOG_PATH = Path("logs/audit.jsonl")

@router.get("/recent")
async def get_recent_audit_logs(
    limit: int = 20, principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """View recent audit events (admin only)"""
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")

    if not DEFAULT_LOG_PATH.exists():
        return {
            "count": 0,
            "events": [],
            "note": "Log file not found",
        }

    # Read last N lines from audit.jsonl
    logs = []
    try:
        with open(DEFAULT_LOG_PATH, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-limit:]:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

    return {
        "count": len(logs),
        "events": logs,
        "note": "PII automatically redacted in logs",
    }
