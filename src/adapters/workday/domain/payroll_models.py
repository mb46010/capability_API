from datetime import date
from typing import Optional
from pydantic import BaseModel

class Money(BaseModel):
    amount: float
    currency: str = "USD"

class BaseSalary(BaseModel):
    amount: float
    currency: str = "USD"
    frequency: str = "ANNUAL"

class BonusTarget(BaseModel):
    percentage: float
    amount: float

class EquityGrant(BaseModel):
    grant_value: float
    vesting_schedule: str

class CompensationDetails(BaseModel):
    base_salary: BaseSalary
    bonus_target: Optional[BonusTarget] = None
    equity: Optional[EquityGrant] = None
    total_compensation: float

class Compensation(BaseModel):
    employee_id: str
    compensation: CompensationDetails
    pay_grade: str
    effective_date: date
    next_review_date: Optional[date] = None

class PayPeriod(BaseModel):
    start: date
    end: date

class Earnings(BaseModel):
    regular: float
    overtime: float = 0
    bonus: float = 0
    gross: float

class Deductions(BaseModel):
    federal_tax: float
    state_tax: float
    social_security: float
    medicare: float
    health_insurance: float
    retirement_401k: float
    total: float

class YearToDate(BaseModel):
    gross: float
    taxes: float
    net: float

class PayStatement(BaseModel):
    statement_id: str
    employee_id: str
    pay_period: PayPeriod
    pay_date: date
    earnings: Earnings
    deductions: Deductions
    net_pay: float
    ytd: YearToDate
