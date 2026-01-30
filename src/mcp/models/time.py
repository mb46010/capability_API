from pydantic import BaseModel
from typing import List, Optional
from datetime import date, datetime

class BalanceEntry(BaseModel):
    type: str
    type_name: str
    available_hours: float
    used_hours: float
    pending_hours: float

class Balance(BaseModel):
    employee_id: str
    balances: List[BalanceEntry]

class TimeOffRequest(BaseModel):
    request_id: str
    employee_id: str
    employee_name: str
    status: str
    type: str
    type_name: str
    start_date: date
    end_date: date
    hours: float
    submitted_at: datetime
    approved_at: Optional[datetime] = None
    approved_by: Optional[dict] = None
