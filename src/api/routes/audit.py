# src/api/routes/audit.py

from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_current_principal
from src.adapters.auth import VerifiedPrincipal
import json

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/audit/recent")
async def get_recent_audit_logs(
    limit: int = 20, principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """View recent audit events (admin only)"""
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(403, "Admin access required")

    # Read last N lines from audit.jsonl
    logs = []
    with open("logs/audit.jsonl") as f:
        for line in f.readlines()[-limit:]:
            logs.append(json.loads(line))

    return {
        "count": len(logs),
        "events": logs,
        "note": "PII automatically redacted in logs",
    }
