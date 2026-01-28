# Data Model: Workday Actions

## Domain Entities

### Shared Types

```python
class EmployeeReference(BaseModel):
    employee_id: str
    display_name: str

class Money(BaseModel):
    amount: float
    currency: str
    frequency: Optional[str] = None
```

## Action Schemas

### 1. HCM Domain

#### `get_employee`
**Input**:
```python
class GetEmployeeRequest(BaseModel):
    employee_id: str
```
**Output**:
```python
class Employee(BaseModel):
    employee_id: str
    name: Name  # {first, last, display}
    email: str
    job: JobDetails  # {title, department, location}
    manager: Optional[EmployeeReference]
    status: str
```

#### `get_manager_chain`
**Input**:
```python
class GetManagerChainRequest(BaseModel):
    employee_id: str
```
**Output**:
```python
class ManagerNode(BaseModel):
    employee_id: str
    display_name: str
    title: str
    level: int

class ManagerChainResponse(BaseModel):
    employee_id: str
    chain: List[ManagerNode]
```

#### `list_direct_reports`
**Input**:
```python
class ListDirectReportsRequest(BaseModel):
    manager_id: str
```
**Output**:
```python
class DirectReport(BaseModel):
    employee_id: str
    display_name: str
    title: str
    start_date: date

class DirectReportsResponse(BaseModel):
    manager_id: str
    direct_reports: List[DirectReport]
    count: int
```

#### `update_contact_info`
**Input**:
```python
class Phone(BaseModel):
    mobile: Optional[str]

class ContactUpdates(BaseModel):
    personal_email: Optional[EmailStr]
    phone: Optional[Phone]

class UpdateContactInfoRequest(BaseModel):
    employee_id: str
    updates: ContactUpdates
```
**Output**:
```python
class FieldChange(BaseModel):
    field: str
    old_value: Any
    new_value: Any

class UpdateContactInfoResponse(BaseModel):
    employee_id: str
    transaction_id: str
    status: str # APPLIED
    effective_date: date
    changes: List[FieldChange]
```

### 2. Time Domain

#### `get_balance`
**Input**:
```python
class GetBalanceRequest(BaseModel):
    employee_id: str
    as_of_date: date = Field(default_factory=date.today)
```
**Output**:
```python
class Balance(BaseModel):
    type: str # PTO, SICK
    type_name: str
    available_hours: float
    used_hours: float
    pending_hours: float

class BalanceResponse(BaseModel):
    employee_id: str
    balances: List[Balance]
```

#### `request` (Time Off)
**Input**:
```python
class TimeOffRequest(BaseModel):
    employee_id: str
    type: str # PTO, SICK
    start_date: date
    end_date: date
    hours: float
    notes: Optional[str]
```
**Output**:
```python
class TimeOffResponse(BaseModel):
    request_id: str
    status: str # PENDING
    submitted_at: datetime
    approver: Optional[EmployeeReference]
    estimated_balance_after: float
```

#### `cancel`
**Input**:
```python
class CancelTimeOffRequest(BaseModel):
    request_id: str
    reason: Optional[str]
```
**Output**:
```python
class CancelTimeOffResponse(BaseModel):
    request_id: str
    status: str # CANCELLED
    cancelled_at: datetime
    cancelled_by: str
    hours_restored: float
```

#### `approve`
**Input**:
```python
class ApproveTimeOffRequest(BaseModel):
    request_id: str
    approver_id: str
    comments: Optional[str]
```
**Output**:
```python
class ApproveTimeOffResponse(BaseModel):
    request_id: str
    status: str # APPROVED
    approved_at: datetime
    approved_by: str
```

### 3. Payroll Domain

#### `get_compensation`
**Input**:
```python
class GetCompensationRequest(BaseModel):
    employee_id: str
```
**Output**:
```python
class CompensationDetails(BaseModel):
    base_salary: Money
    bonus_target: Optional[Bonus]
    total_compensation: float

class CompensationResponse(BaseModel):
    employee_id: str
    compensation: CompensationDetails
    pay_grade: str
    effective_date: date
```
