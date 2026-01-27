from datetime import date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from src.adapters.workday.domain.types import EmployeeStatus, EmployeeType

class EmployeeName(BaseModel):
    first: str = Field(description="Employee's given name")
    last: str = Field(description="Employee's family name")
    display: str = Field(description="Full name formatted for display")
    legal_first: Optional[str] = Field(None, description="Sensitive: Legal given name")
    legal_last: Optional[str] = Field(None, description="Sensitive: Legal family name")

class EmployeeJob(BaseModel):
    title: str = Field(description="Current job title")
    department: str = Field(description="Name of the department")
    department_id: str = Field(description="Unique identifier for the department (e.g., DEPT-ENG)")
    location: str = Field(description="Primary office or remote work location")
    cost_center: Optional[str] = Field(None, description="Financial identifier for charging expenses")
    employee_type: Optional[EmployeeType] = Field(None, description="Type of employment (FULL_TIME, PART_TIME, etc.)")

class EmployeePhone(BaseModel):
    work: Optional[str] = Field(None, description="Office telephone number")
    mobile: Optional[str] = Field(None, description="Sensitive: Personal or business mobile number")

class EmployeeAddress(BaseModel):
    street: str = Field(description="Street name and number")
    city: str = Field(description="City or locality")
    state: str = Field(description="State, province, or region")
    postal_code: str = Field(description="ZIP or postal code")
    country: str = Field(description="ISO country code or name")

class EmergencyContact(BaseModel):
    name: str = Field(description="Full name of the contact person")
    relationship: str = Field(description="Relationship to the employee (e.g., Spouse, Parent)")
    phone: str = Field(description="Telephone number for the contact")

class ManagerRef(BaseModel):
    employee_id: str = Field(description="Unique identifier for the manager")
    display_name: str = Field(description="Full name of the manager")

class Employee(BaseModel):
    employee_id: str = Field(description="Unique identifier for the employee (e.g., EMP001)")
    name: EmployeeName = Field(description="Structured name object")
    email: EmailStr = Field(description="Primary work email address")
    job: EmployeeJob = Field(description="Current job and department details")
    manager: Optional[ManagerRef] = Field(None, description="Reference to the direct manager")
    status: EmployeeStatus = Field(description="Current employment status (ACTIVE, ON_LEAVE, etc.)")
    start_date: date = Field(description="Initial date of hire")

class EmployeeFull(Employee):
    personal_email: Optional[EmailStr] = Field(None, description="Sensitive: Personal non-work email")
    phone: Optional[EmployeePhone] = Field(None, description="Sensitive: Structured phone numbers")
    birth_date: Optional[date] = Field(None, description="Sensitive: Employee's date of birth")
    national_id_last_four: Optional[str] = Field(None, description="Sensitive: Last 4 digits of government ID")
    address: Optional[EmployeeAddress] = Field(None, description="Sensitive: Primary residential address")
    emergency_contact: Optional[EmergencyContact] = Field(None, description="Sensitive: Primary emergency contact")

class Department(BaseModel):
    department_id: str = Field(description="Unique identifier for the department")
    name: str = Field(description="Human-readable department name")
    cost_center: str = Field(description="Budget code associated with this department")
    parent_id: Optional[str] = Field(None, description="ID of the parent department in the hierarchy")
    head_id: Optional[str] = Field(None, description="Employee ID of the department head")
