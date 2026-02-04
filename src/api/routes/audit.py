import json
import os
from pathlib import Path
from collections import deque
from fastapi import APIRouter, Depends, HTTPException
from src.api.dependencies import get_current_principal
from src.adapters.auth import VerifiedPrincipal

from src.lib.config_validator import settings

router = APIRouter(prefix="/audit", tags=["audit"])

MAX_AUDIT_LOG_LIMIT = 500

@router.get("/recent")
async def get_recent_audit_logs(
    limit: int = 20, principal: VerifiedPrincipal = Depends(get_current_principal)
):
    """View recent audit events (admin only)"""
    if not principal.has_group("hr-platform-admins"):
        raise HTTPException(status_code=403, detail="Admin access required")

    log_path = Path(settings.AUDIT_LOG_PATH)
    if not log_path.exists():
        return {
            "count": 0,
            "events": [],
            "note": f"Log file not found at {log_path}",
        }

    # Enforce maximum limit
    safe_limit = max(1, min(limit, MAX_AUDIT_LOG_LIMIT))

    # Read last N lines from audit.jsonl efficiently
    logs = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            # deque with maxlen efficiently keeps only the last N items
            tail = deque(f, maxlen=safe_limit)
            for line in tail:
                if line.strip():
                    logs.append(json.loads(line))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading logs: {str(e)}")

    # Reverse to show most recent first (last lines are most recent in jsonl)
    logs.reverse()

    return {
        "count": len(logs),
        "events": logs,
        "note": "PII automatically redacted in logs",
    }
