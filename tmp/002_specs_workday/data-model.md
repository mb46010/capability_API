# Data Model: Workday Connector

**Document**: `specs/workday-connector/data-model.md`  
**Status**: Draft  
**Created**: 2026-01-27

---

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐
│    Employee     │──────▶│   Department    │
├─────────────────┤       ├─────────────────┤
│ employee_id PK  │       │ department_id PK│
│ name{}          │       │ name            │
│ email           │       │ cost_center     │
│ job{}           │       │ parent_id FK    │
│ manager_id FK   │───┐   │ head_id FK      │
│ department_id FK│   │   └─────────────────┘
│ status          │   │
│ start_date      │   │   ┌─────────────────┐
│ [sensitive]     │   └──▶│    Employee     │ (self-reference)
└────────┬────────┘       └─────────────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐       ┌─────────────────┐
│ TimeOffRequest  │       │  TimeOffType    │
├─────────────────┤       ├─────────────────┤
│ request_id PK   │       │ type_code PK    │
│ employee_id FK  │       │ name            │
│ type FK         │──────▶│ accrual_rate    │
│ status          │       │ max_carryover   │
│ start_date      │       └─────────────────┘
│ end_date        │
│ hours           │       ┌─────────────────┐
│ approver_id FK  │──────▶│    Employee     │
│ submitted_at    │       └─────────────────┘
│ approved_at     │
└────────┬────────┘
         │
         │ 1:N
         ▼
┌─────────────────┐
│ TimeOffBalance  │
├─────────────────┤
│ employee_id FK  │
│ type FK         │
│ available_hours │
│ used_hours      │
│ pending_hours   │
│ as_of_date      │
└─────────────────┘

┌─────────────────┐       ┌─────────────────┐
│  Compensation   │       │  PayStatement   │
├─────────────────┤       ├─────────────────┤
│ employee_id FK  │       │ statement_id PK │
│ base_salary{}   │       │ employee_id FK  │
│ bonus_target{}  │       │ pay_period{}    │
│ equity{}        │       │ pay_date        │
│ pay_grade       │       │ earnings{}      │
│ effective_date  │       │ deductions{}    │
└─────────────────┘       │ net_pay         │
                          └─────────────────┘
```

---

## Core Entities

### Employee

The central entity representing a worker in the organization.

```python
class EmployeeName(BaseModel):
    first: str
    last: str
    display: str
    legal_first: Optional[str] = None  # Sensitive
    legal_last: Optional[str] = None   # Sensitive

class EmployeeJob(BaseModel):
    title: str
    department: str
    department_id: str
    location: str
    cost_center: Optional[str] = None
    employee_type: Optional[str] = None  # FULL_TIME, PART_TIME, CONTRACTOR

class EmployeePhone(BaseModel):
    work: Optional[str] = None
    mobile: Optional[str] = None  # Sensitive

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

class EmployeeStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ON_LEAVE = "ON_LEAVE"
    TERMINATED = "TERMINATED"

class Employee(BaseModel):
    """Public employee record - safe for general access."""
    employee_id: str
    name: EmployeeName
    email: str
    job: EmployeeJob
    manager: Optional[ManagerRef] = None
    status: EmployeeStatus
    start_date: date

class EmployeeFull(Employee):
    """Complete employee record - contains sensitive PII."""
    personal_email: Optional[str] = None
    phone: Optional[EmployeePhone] = None
    birth_date: Optional[date] = None
    national_id_last_four: Optional[str] = None
    address: Optional[EmployeeAddress] = None
    emergency_contact: Optional[EmergencyContact] = None
    
    class Config:
        # Mark sensitive fields for audit logging
        sensitive_fields = [
            "personal_email",
            "phone.mobile", 
            "birth_date",
            "national_id_last_four",
            "address",
            "emergency_contact"
        ]
```

### Field Sensitivity Classification

| Field | Sensitivity | Access Level |
|-------|-------------|--------------|
| employee_id | Public | All |
| name.display | Public | All |
| name.first, name.last | Public | All |
| name.legal_* | PII | HR Admin |
| email (work) | Internal | Authenticated |
| personal_email | PII | Self, HR Admin |
| phone.work | Internal | Authenticated |
| phone.mobile | PII | Self, HR Admin, Manager |
| job.* | Internal | Authenticated |
| birth_date | PII | Self, HR Admin |
| national_id_last_four | Sensitive PII | Self, HR Admin |
| address | PII | Self, HR Admin |
| emergency_contact | PII | Self, HR Admin, Manager |
| salary, compensation | Confidential | Self, HR Admin, Manager (with approval) |

---

### Department

Organizational unit for grouping employees.

```python
class Department(BaseModel):
    department_id: str
    name: str
    cost_center: str
    parent_id: Optional[str] = None  # For nested org structure
    head_id: Optional[str] = None     # Department head employee_id
    
class DepartmentTree(BaseModel):
    """Hierarchical department structure."""
    department: Department
    children: List["DepartmentTree"] = []
    employee_count: int
```

---

### Time Off

#### TimeOffType

```python
class TimeOffType(BaseModel):
    type_code: str  # PTO, SICK, BEREAVEMENT, JURY_DUTY, etc.
    name: str
    accrual_rate_per_period: float  # Hours per pay period
    max_carryover: int              # Hours that can roll over
    requires_approval: bool = True
    min_notice_days: int = 0        # Days in advance required
```

**Standard Types**:
| Code | Name | Accrual | Max Carryover |
|------|------|---------|---------------|
| PTO | Paid Time Off | 6.67 hrs/period | 40 hrs |
| SICK | Sick Leave | 4 hrs/period | 80 hrs |
| BEREAVEMENT | Bereavement | N/A (as needed) | 0 |
| JURY | Jury Duty | N/A (as needed) | 0 |
| PARENTAL | Parental Leave | N/A (policy-based) | 0 |

#### TimeOffBalance

```python
class TimeOffBalance(BaseModel):
    type: str
    type_name: str
    available_hours: float
    used_hours: float
    pending_hours: float  # Approved but not yet taken
    accrual_rate_per_period: float
    max_carryover: int
```

#### TimeOffRequest

```python
class TimeOffRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    CANCELLED = "CANCELLED"

class TimeOffRequestHistory(BaseModel):
    action: str  # SUBMITTED, APPROVED, DENIED, CANCELLED
    timestamp: datetime
    actor: str   # employee_id

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
```

---

### Compensation

```python
class Money(BaseModel):
    amount: float
    currency: str = "USD"

class BaseSalary(BaseModel):
    amount: float
    currency: str = "USD"
    frequency: str = "ANNUAL"  # ANNUAL, MONTHLY, HOURLY

class BonusTarget(BaseModel):
    percentage: float  # Percentage of base
    amount: float      # Calculated amount

class EquityGrant(BaseModel):
    grant_value: float
    vesting_schedule: str

class Compensation(BaseModel):
    """Highly sensitive compensation data."""
    employee_id: str
    compensation: CompensationDetails
    pay_grade: str
    effective_date: date
    next_review_date: Optional[date] = None
    
class CompensationDetails(BaseModel):
    base_salary: BaseSalary
    bonus_target: Optional[BonusTarget] = None
    equity: Optional[EquityGrant] = None
    total_compensation: float  # Calculated total
```

---

### Pay Statement

```python
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
```

---

## Fixture Data Structure

Fixtures are stored as YAML for easy editing:

```
fixtures/workday/
├── employees.yaml
├── departments.yaml
├── time_off_types.yaml
├── time_off_balances.yaml
├── time_off_requests.yaml
├── compensation.yaml
└── pay_statements.yaml
```

### employees.yaml

```yaml
employees:
  EMP001:
    employee_id: "EMP001"
    name:
      first: "Alice"
      last: "Johnson"
      display: "Alice Johnson"
      legal_first: "Alice Marie"
      legal_last: "Johnson"
    email: "alice.johnson@example.com"
    personal_email: "alice.j@gmail.com"
    phone:
      work: "+1-555-0101"
      mobile: "+1-555-0102"
    job:
      title: "Senior Engineer"
      department: "Engineering"
      department_id: "DEPT-ENG"
      location: "San Francisco"
      cost_center: "CC-1001"
      employee_type: "FULL_TIME"
    manager_id: "EMP042"
    status: "ACTIVE"
    start_date: "2022-03-15"
    birth_date: "1990-05-22"
    national_id_last_four: "1234"
    address:
      street: "123 Main St"
      city: "San Francisco"
      state: "CA"
      postal_code: "94102"
      country: "USA"
    emergency_contact:
      name: "John Johnson"
      relationship: "Spouse"
      phone: "+1-555-0199"

  EMP042:
    employee_id: "EMP042"
    name:
      first: "Bob"
      last: "Martinez"
      display: "Bob Martinez"
    email: "bob.martinez@example.com"
    job:
      title: "Engineering Manager"
      department: "Engineering"
      department_id: "DEPT-ENG"
      location: "San Francisco"
      employee_type: "FULL_TIME"
    manager_id: "EMP100"
    status: "ACTIVE"
    start_date: "2019-08-01"

  EMP100:
    employee_id: "EMP100"
    name:
      first: "Carol"
      last: "Chen"
      display: "Carol Chen"
    email: "carol.chen@example.com"
    job:
      title: "VP of Engineering"
      department: "Engineering"
      department_id: "DEPT-ENG"
      location: "San Francisco"
      employee_type: "FULL_TIME"
    manager_id: "EMP200"
    status: "ACTIVE"
    start_date: "2018-01-15"

  EMP200:
    employee_id: "EMP200"
    name:
      first: "Diana"
      last: "Ross"
      display: "Diana Ross"
    email: "diana.ross@example.com"
    job:
      title: "CEO"
      department: "Executive"
      department_id: "DEPT-EXEC"
      location: "San Francisco"
      employee_type: "FULL_TIME"
    manager_id: null  # Top of org
    status: "ACTIVE"
    start_date: "2015-01-01"

  EMP003:
    employee_id: "EMP003"
    name:
      first: "Charlie"
      last: "Brown"
      display: "Charlie Brown"
    email: "charlie.brown@example.com"
    job:
      title: "Engineer"
      department: "Engineering"
      department_id: "DEPT-ENG"
      location: "Remote"
      employee_type: "FULL_TIME"
    manager_id: "EMP042"
    status: "ACTIVE"
    start_date: "2023-06-01"
```

### departments.yaml

```yaml
departments:
  DEPT-EXEC:
    department_id: "DEPT-EXEC"
    name: "Executive"
    cost_center: "CC-0001"
    parent_id: null
    head_id: "EMP200"

  DEPT-ENG:
    department_id: "DEPT-ENG"
    name: "Engineering"
    cost_center: "CC-1000"
    parent_id: "DEPT-EXEC"
    head_id: "EMP100"

  DEPT-HR:
    department_id: "DEPT-HR"
    name: "Human Resources"
    cost_center: "CC-2000"
    parent_id: "DEPT-EXEC"
    head_id: "EMP150"
```

### time_off_balances.yaml

```yaml
balances:
  EMP001:
    - type: "PTO"
      type_name: "Paid Time Off"
      available_hours: 120
      used_hours: 40
      pending_hours: 8
      accrual_rate_per_period: 6.67
      max_carryover: 40
    - type: "SICK"
      type_name: "Sick Leave"
      available_hours: 48
      used_hours: 16
      pending_hours: 0
      accrual_rate_per_period: 4
      max_carryover: 80

  EMP042:
    - type: "PTO"
      available_hours: 160
      used_hours: 24
      pending_hours: 0
      accrual_rate_per_period: 8.33  # More senior = higher accrual
      max_carryover: 80
```

### time_off_requests.yaml

```yaml
requests:
  TOR-001:
    request_id: "TOR-001"
    employee_id: "EMP001"
    type: "PTO"
    status: "APPROVED"
    start_date: "2026-02-10"
    end_date: "2026-02-14"
    hours: 40
    notes: "Family vacation"
    submitted_at: "2026-01-15T10:30:00Z"
    approved_by: "EMP042"
    approved_at: "2026-01-16T09:00:00Z"

  TOR-002:
    request_id: "TOR-002"
    employee_id: "EMP001"
    type: "PTO"
    status: "PENDING"
    start_date: "2026-04-20"
    end_date: "2026-04-22"
    hours: 24
    submitted_at: "2026-01-25T14:00:00Z"
```

### compensation.yaml

```yaml
compensation:
  EMP001:
    base_salary:
      amount: 185000
      currency: "USD"
      frequency: "ANNUAL"
    bonus_target:
      percentage: 15
      amount: 27750
    equity:
      grant_value: 50000
      vesting_schedule: "4 years with 1 year cliff"
    total_compensation: 262750
    pay_grade: "L5"
    effective_date: "2025-01-01"
    next_review_date: "2026-01-01"

  EMP042:
    base_salary:
      amount: 220000
      currency: "USD"
      frequency: "ANNUAL"
    bonus_target:
      percentage: 20
      amount: 44000
    equity:
      grant_value: 100000
      vesting_schedule: "4 years with 1 year cliff"
    total_compensation: 364000
    pay_grade: "M2"
    effective_date: "2025-01-01"
```

---

## Manager Chain Computation

For operations that need the management hierarchy:

```python
def get_manager_chain(employee_id: str, employees: dict) -> List[str]:
    """Returns list of manager IDs from direct manager to CEO."""
    chain = []
    current_id = employees[employee_id].manager_id
    
    while current_id:
        chain.append(current_id)
        current_id = employees.get(current_id, {}).manager_id
    
    return chain

def is_manager_of(potential_manager_id: str, employee_id: str, employees: dict) -> bool:
    """Check if potential_manager is in employee's manager chain."""
    return potential_manager_id in get_manager_chain(employee_id, employees)
```

---

## ID Generation

For new entities created by the simulation:

```python
def generate_employee_id() -> str:
    return f"EMP{random.randint(1000, 9999)}"

def generate_request_id() -> str:
    return f"TOR-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

def generate_transaction_id() -> str:
    return f"TXN-{datetime.now().strftime('%Y%m%d')}-{random.randint(100, 999)}"

def generate_statement_id(year: int, period: int) -> str:
    return f"PAY-{year}-{period:02d}"
```
