from datetime import date
from typing import Optional
from pydantic import BaseModel, Field

class Money(BaseModel):
    amount: float = Field(description="Numerical value of the currency")
    currency: str = Field(default="USD", description="ISO currency code (e.g., USD, EUR)")

class BaseSalary(BaseModel):
    amount: float = Field(description="Gross salary amount before deductions")
    currency: str = Field(default="USD", description="Currency of the salary")
    frequency: str = Field(default="ANNUAL", description="Pay frequency (e.g., ANNUAL, MONTHLY)")

class BonusTarget(BaseModel):
    percentage: float = Field(description="Target bonus as a percentage of base salary")
    amount: float = Field(description="Calculated target bonus amount")

class EquityGrant(BaseModel):
    grant_value: float = Field(description="Estimated value of the equity at time of grant")
    vesting_schedule: str = Field(description="Human-readable description of the vesting terms")

class CompensationDetails(BaseModel):
    base_salary: BaseSalary = Field(description="Primary salary information")
    bonus_target: Optional[BonusTarget] = Field(None, description="Bonus incentive details")
    equity: Optional[EquityGrant] = Field(None, description="Stock or equity grant details")
    total_compensation: float = Field(description="Aggregated annual value of all compensation components")

class Compensation(BaseModel):
    employee_id: str = Field(description="ID of the employee this compensation record belongs to")
    compensation: CompensationDetails = Field(description="Detailed breakdown of pay and benefits")
    pay_grade: str = Field(description="Job level identifier (e.g., L5, M2)")
    effective_date: date = Field(description="When this compensation structure became active")
    next_review_date: Optional[date] = Field(None, description="Planned date for the next salary review")

class PayPeriod(BaseModel):
    start: date = Field(description="First day of the period")
    end: date = Field(description="Last day of the period")

class Earnings(BaseModel):
    regular: float = Field(description="Base pay for regular hours")
    overtime: float = Field(default=0, description="Additional pay for hours beyond standard")
    bonus: float = Field(default=0, description="Bonus payments included in this statement")
    gross: float = Field(description="Total earnings before deductions and taxes")

class Deductions(BaseModel):
    federal_tax: float = Field(description="Federal income tax withholding")
    state_tax: float = Field(description="State or local income tax withholding")
    social_security: float = Field(description="Social Security / OASDI contribution")
    medicare: float = Field(description="Medicare contribution")
    health_insurance: float = Field(description="Employee portion of health insurance premiums")
    retirement_401k: float = Field(description="Pre-tax 401k or retirement contributions")
    total: float = Field(description="Sum of all deductions and withholdings")

class YearToDate(BaseModel):
    gross: float = Field(description="Total gross earnings for the calendar year")
    taxes: float = Field(description="Total taxes withheld for the calendar year")
    net: float = Field(description="Total take-home pay for the calendar year")

class PayStatement(BaseModel):
    statement_id: str = Field(description="Unique identifier for the pay statement")
    employee_id: str = Field(description="ID of the employee")
    pay_period: PayPeriod = Field(description="The date range covered by this statement")
    pay_date: date = Field(description="The date the funds are issued to the employee")
    earnings: Earnings = Field(description="Breakdown of gross income")
    deductions: Deductions = Field(description="Breakdown of taxes and withholdings")
    net_pay: float = Field(description="Actual take-home amount for this statement")
    ytd: YearToDate = Field(description="Year-to-date cumulative totals")
