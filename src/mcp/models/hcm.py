from pydantic import BaseModel, Field
from typing import List, Optional

class Name(BaseModel):
    first: str
    last: str
    display: str

class Job(BaseModel):
    title: str
    department: str
    location: str

class Manager(BaseModel):
    employee_id: str
    display_name: str

class Employee(BaseModel):
    employee_id: str
    name: Name
    personal_email: Optional[str] = None
    phone: Optional[dict] = None
    job: Job
    manager: Optional[Manager] = None
    status: str

class OrgNode(BaseModel):
    employee_id: str
    name: str
    title: str
    reports: List['OrgNode'] = []

class OrgChart(BaseModel):
    root: OrgNode
    total_count: int

class ManagerChainLink(BaseModel):
    employee_id: str
    display_name: str
    title: str
    level: int

class ManagerChain(BaseModel):
    employee_id: str
    chain: List[ManagerChainLink]
