from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field

class FlowStartRequest(BaseModel):
    parameters: Dict[str, Any] = Field(description="Initial data required to start the workflow")
    callback_url: Optional[HttpUrl] = Field(default=None, description="Optional URL to notify when the flow completes or requires input")

class FlowStatusResponse(BaseModel):
    flow_id: str = Field(description="Unique identifier for the long-running process")
    status: str = Field(description="Current state of the flow (e.g., RUNNING, COMPLETED, FAILED)")
    start_time: Optional[datetime] = Field(default=None, description="When the flow was initially triggered")
    current_step: Optional[str] = Field(default=None, description="The name of the currently active workflow step")
    result: Optional[Dict[str, Any]] = Field(default=None, description="Final output data if the flow is COMPLETED")
    error: Optional[str] = Field(default=None, description="Error message if the flow FAILED")
