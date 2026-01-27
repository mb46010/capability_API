from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from src.adapters.workday.domain.types import TimeOffRequestStatus
from src.adapters.workday.domain.hcm_models import ManagerRef

class TimeOffType(BaseModel):
    type_code: str = Field(description="Internal code for the leave type (e.g., PTO, SICK)")
    name: str = Field(description="Human-readable name of the leave type")
    accrual_rate_per_period: float = Field(description="Hours earned per pay period")
    max_carryover: int = Field(description="Maximum hours that can be rolled over to the next year")
    requires_approval: bool = Field(default=True, description="If true, requests must be approved by a manager")
    min_notice_days: int = Field(default=0, description="Minimum days in advance a request must be submitted")

class TimeOffBalance(BaseModel):
    type: str = Field(description="Code of the leave type")
    type_name: str = Field(description="Human-readable name of the leave type")
    available_hours: float = Field(description="Current balance available for use")
    used_hours: float = Field(description="Total hours used in the current period")
    pending_hours: float = Field(description="Hours requested but not yet taken or approved")
    accrual_rate_per_period: float = Field(description="Current accrual rate")
    max_carryover: int = Field(description="Current carryover limit")

class TimeOffRequestHistory(BaseModel):
    action: str = Field(description="Action performed (e.g., SUBMITTED, APPROVED)")
    timestamp: datetime = Field(description="When the action was performed")
    actor: str = Field(description="Principal ID who performed the action")

class TimeOffRequest(BaseModel):
    request_id: str = Field(description="Unique identifier for the request")
    employee_id: str = Field(description="ID of the employee making the request")
    employee_name: Optional[str] = Field(None, description="Full name of the employee")
    type: str = Field(description="The requested leave type code")
    type_name: Optional[str] = Field(None, description="Human-readable name of the leave type")
    status: TimeOffRequestStatus = Field(description="Current state of the request")
    start_date: date = Field(description="First day of the requested leave")
    end_date: date = Field(description="Last day of the requested leave")
    hours: float = Field(description="Total number of hours requested")
    notes: Optional[str] = Field(None, description="Optional comments from the requester")
    submitted_at: datetime = Field(description="When the request was initially created")
    approved_by: Optional[ManagerRef] = Field(None, description="Reference to the approving manager")
    approved_at: Optional[datetime] = Field(None, description="When the request was approved")
    history: List[TimeOffRequestHistory] = Field(default=[], description="Audit trail of actions performed on this request")
