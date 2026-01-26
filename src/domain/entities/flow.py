from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl

class FlowStartRequest(BaseModel):
    parameters: Dict[str, Any]
    callback_url: Optional[HttpUrl] = None

class FlowStatusResponse(BaseModel):
    flow_id: str
    status: str  # RUNNING, COMPLETED, FAILED, WAITING_FOR_INPUT
    start_time: Optional[datetime] = None
    current_step: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
