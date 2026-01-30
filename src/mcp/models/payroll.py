from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class BaseSalary(BaseModel):
    amount: float
    currency: str
    frequency: str

class BonusTarget(BaseModel):
    percentage: float
    amount: float

class CompensationData(BaseModel):
    base_salary: BaseSalary
    bonus_target: Optional[BonusTarget] = None
    total_compensation: float

class Compensation(BaseModel):
    employee_id: str
    compensation: CompensationData
    pay_grade: str
    effective_date: date

class PayStatement(BaseModel):
    statement_id: str
    employee_id: str
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    gross_pay: float
    net_pay: float
    currency: str
