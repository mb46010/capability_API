from datetime import date
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from src.adapters.workday.domain.types import EmployeeStatus, EmployeeType

class EmployeeName(BaseModel):
    first: str
    last: str
    display: str
    legal_first: Optional[str] = None
    legal_last: Optional[str] = None

class EmployeeJob(BaseModel):
    title: str
    department: str
    department_id: str
    location: str
    cost_center: Optional[str] = None
    employee_type: Optional[EmployeeType] = None

class EmployeePhone(BaseModel):
    work: Optional[str] = None
    mobile: Optional[str] = None

class EmployeeAddress(BaseModel):
    street: str
    city: str
    state: str
    postal_code: str
    country: str

class EmergencyContact(BaseModel):
    name: str
    relationship: str
    phone: str

class ManagerRef(BaseModel):
    employee_id: str
    display_name: str

class Employee(BaseModel):
    employee_id: str
    name: EmployeeName
    email: EmailStr
    job: EmployeeJob
    manager: Optional[ManagerRef] = None
    status: EmployeeStatus
    start_date: date

class EmployeeFull(Employee):
    personal_email: Optional[EmailStr] = None
    phone: Optional[EmployeePhone] = None
    birth_date: Optional[date] = None
    national_id_last_four: Optional[str] = None
    address: Optional[EmployeeAddress] = None
    emergency_contact: Optional[EmergencyContact] = None

class Department(BaseModel):
    department_id: str
    name: str
    cost_center: str
    parent_id: Optional[str] = None
    head_id: Optional[str] = None
