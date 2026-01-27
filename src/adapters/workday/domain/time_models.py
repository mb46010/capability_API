from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel
from src.adapters.workday.domain.types import TimeOffRequestStatus
from src.adapters.workday.domain.hcm_models import ManagerRef

class TimeOffType(BaseModel):
    type_code: str
    name: str
    accrual_rate_per_period: float
    max_carryover: int
    requires_approval: bool = True
    min_notice_days: int = 0

class TimeOffBalance(BaseModel):
    type: str
    type_name: str
    available_hours: float
    used_hours: float
    pending_hours: float
    accrual_rate_per_period: float
    max_carryover: int

class TimeOffRequestHistory(BaseModel):
    action: str
    timestamp: datetime
    actor: str

class TimeOffRequest(BaseModel):
    request_id: str
    employee_id: str
    employee_name: Optional[str] = None
    type: str
    type_name: Optional[str] = None
    status: TimeOffRequestStatus
    start_date: date
    end_date: date
    hours: float
    notes: Optional[str] = None
    submitted_at: datetime
    approved_by: Optional[ManagerRef] = None
    approved_at: Optional[datetime] = None
    history: List[TimeOffRequestHistory] = []
