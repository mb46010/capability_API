# Workday Connector Specification

**Document**: `specs/workday-connector/spec.md`  
**Status**: Draft  
**Created**: 2026-01-27  
**Purpose**: Simulated Workday connector for development, auth stress testing, and MCP server generation

---

## Clarifications

### Session 2026-01-27
- Q: How should the simulator handle data persistence for write operations (updates, terminations)? → A: **In-memory only** (Reset on restart): Changes live only in RAM; fresh start reloads fixtures.
- Q: What authentication mechanism should the simulator require? → A: **Passthrough (Trust policy engine)**: Assume caller is already authenticated/authorized; simulator checks `principal` context only for auditing.
- Q: Which programming interface should the simulator implement? → A: **Generic `execute`**: Implement `ConnectorPort.execute(action, params)` where `action` is the capability string, ensuring compatibility with the existing domain logic.
- Q: How should the principal context be passed to the connector's execute method? → A: **Inject via `parameters`**: Include `__principal__` (and optionally `__groups__`, `__type__`) in the parameters dictionary passed to the port.
- Q: How should the simulator's in-memory state handle concurrent write operations? → A: **Single-threaded asyncio (No locks)**: Rely on asyncio's single-threaded nature; no explicit locks for memory state updates.

## Overview

This connector simulates Workday's HCM, Time Tracking, and Payroll APIs with realistic data models, response shapes, and latency profiles. It serves as a drop-in replacement for the real Workday integration during development.

### Design Goals

1. **Auth stress testing**: Every operation requires specific capabilities; policy enforcement is the primary test target.
2. **Realistic schemas**: Response shapes match what real Workday APIs return (simplified).
3. **MCP-ready**: Operations map cleanly to MCP tool definitions.
4. **Swappable**: Interface allows real Workday adapter without changing callers.
5. **Simulated Persistence**: State changes (updates/terminations) are stored in-memory and reset upon application restart.

---

## Technical Interface & Security

### Port Implementation
The simulator implements the `ConnectorPort` interface:
- **Method**: `async def execute(self, action: str, parameters: Dict[str, Any]) -> Dict[str, Any]`
- **Action Mapping**: The `action` parameter corresponds to the capability string (e.g., `workday.hcm.get_employee`).

### Authentication & Context
- **Passthrough Trust**: The simulator assumes the caller is authenticated by the upstream `ActionService`/`PolicyEngine`.
- **Context Injection**: Security context is passed within the `parameters` dictionary under internal keys:
  - `__principal__`: The ID of the authenticated principal.
  - `__groups__`: List of groups assigned to the principal.
  - `__type__`: The type of principal (HUMAN, MACHINE, AI_AGENT).

---

## Capability Mapping

Every operation maps to a capability string used by the policy engine.

### HCM (Human Capital Management)

| Operation | Capability | Principal Types | Sensitive |
|-----------|------------|-----------------|-----------|
| Get Employee | `workday.hcm.get_employee` | HUMAN, MACHINE, AI_AGENT | No |
| Get Employee Full | `workday.hcm.get_employee_full` | HUMAN, MACHINE | Yes (includes PII) |
| List Direct Reports | `workday.hcm.list_direct_reports` | HUMAN, MACHINE, AI_AGENT | No |
| Get Org Chart | `workday.hcm.get_org_chart` | HUMAN, MACHINE, AI_AGENT | No |
| Get Manager Chain | `workday.hcm.get_manager_chain` | HUMAN, MACHINE, AI_AGENT | No |
| Update Employee | `workday.hcm.update_employee` | HUMAN | Yes |
| Terminate Employee | `workday.hcm.terminate_employee` | HUMAN | Yes |

### Time Tracking

| Operation | Capability | Principal Types | Sensitive |
|-----------|------------|-----------------|-----------|
| Get Time Off Balance | `workday.time.get_balance` | HUMAN, MACHINE, AI_AGENT | No |
| List Time Off Requests | `workday.time.list_requests` | HUMAN, MACHINE, AI_AGENT | No |
| Get Time Off Request | `workday.time.get_request` | HUMAN, MACHINE, AI_AGENT | No |
| Request Time Off | `workday.time.request` | HUMAN, AI_AGENT | No |
| Approve Time Off | `workday.time.approve` | HUMAN | No |
| Cancel Time Off | `workday.time.cancel` | HUMAN, AI_AGENT | No |

### Payroll

| Operation | Capability | Principal Types | Sensitive |
|-----------|------------|-----------------|-----------|
| Get Compensation | `workday.payroll.get_compensation` | HUMAN | Yes |
| Get Pay Statement | `workday.payroll.get_pay_statement` | HUMAN | Yes |
| List Pay Statements | `workday.payroll.list_pay_statements` | HUMAN | Yes |

---

## Operations Detail

### HCM Operations

#### `workday.hcm.get_employee`

Returns public employee information suitable for directory lookups.

**Request**:
```json
{
  "employee_id": "EMP001"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "name": {
    "first": "Alice",
    "last": "Johnson",
    "display": "Alice Johnson"
  },
  "email": "alice.johnson@example.com",
  "job": {
    "title": "Senior Engineer",
    "department": "Engineering",
    "department_id": "DEPT-ENG",
    "location": "San Francisco"
  },
  "manager": {
    "employee_id": "EMP042",
    "display_name": "Bob Martinez"
  },
  "status": "ACTIVE",
  "start_date": "2022-03-15"
}
```

**Errors**:
- `EMPLOYEE_NOT_FOUND`: Employee ID does not exist
- `EMPLOYEE_INACTIVE`: Employee is terminated (optional: return limited data)

**Latency**: 50-100ms

---

#### `workday.hcm.get_employee_full`

Returns complete employee record including sensitive PII. Requires elevated access.

**Request**:
```json
{
  "employee_id": "EMP001"
}
```

**Response** (extends get_employee):
```json
{
  "employee_id": "EMP001",
  "name": {
    "first": "Alice",
    "last": "Johnson",
    "display": "Alice Johnson",
    "legal_first": "Alice Marie",
    "legal_last": "Johnson"
  },
  "email": "alice.johnson@example.com",
  "personal_email": "alice.j@gmail.com",
  "phone": {
    "work": "+1-555-0101",
    "mobile": "+1-555-0102"
  },
  "job": {
    "title": "Senior Engineer",
    "department": "Engineering",
    "department_id": "DEPT-ENG",
    "location": "San Francisco",
    "cost_center": "CC-1001",
    "employee_type": "FULL_TIME"
  },
  "manager": {
    "employee_id": "EMP042",
    "display_name": "Bob Martinez"
  },
  "status": "ACTIVE",
  "start_date": "2022-03-15",
  "birth_date": "1990-05-22",
  "national_id_last_four": "1234",
  "address": {
    "street": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "postal_code": "94102",
    "country": "USA"
  },
  "emergency_contact": {
    "name": "John Johnson",
    "relationship": "Spouse",
    "phone": "+1-555-0199"
  }
}
```

**Audit**: Always VERBOSE (sensitive data access)

**Latency**: 100-150ms

---

#### `workday.hcm.list_direct_reports`

Returns employees who report directly to the specified manager.

**Request**:
```json
{
  "manager_id": "EMP042"
}
```

**Response**:
```json
{
  "manager_id": "EMP042",
  "direct_reports": [
    {
      "employee_id": "EMP001",
      "display_name": "Alice Johnson",
      "title": "Senior Engineer",
      "start_date": "2022-03-15"
    },
    {
      "employee_id": "EMP003",
      "display_name": "Charlie Brown",
      "title": "Engineer",
      "start_date": "2023-06-01"
    }
  ],
  "count": 2
}
```

**Latency**: 100-200ms

---

#### `workday.hcm.get_org_chart`

Returns organizational hierarchy starting from a given employee or department.

**Request**:
```json
{
  "root_id": "EMP100",
  "depth": 2
}
```

**Response**:
```json
{
  "root": {
    "employee_id": "EMP100",
    "display_name": "Carol Chen",
    "title": "VP of Engineering",
    "reports": [
      {
        "employee_id": "EMP042",
        "display_name": "Bob Martinez",
        "title": "Engineering Manager",
        "reports": [
          {
            "employee_id": "EMP001",
            "display_name": "Alice Johnson",
            "title": "Senior Engineer",
            "reports": []
          }
        ]
      }
    ]
  },
  "total_count": 3
}
```

**Latency**: 150-250ms

---

#### `workday.hcm.get_manager_chain`

Returns the management chain from employee up to CEO/root.

**Request**:
```json
{
  "employee_id": "EMP001"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "chain": [
    {
      "employee_id": "EMP042",
      "display_name": "Bob Martinez",
      "title": "Engineering Manager",
      "level": 1
    },
    {
      "employee_id": "EMP100",
      "display_name": "Carol Chen",
      "title": "VP of Engineering",
      "level": 2
    },
    {
      "employee_id": "EMP200",
      "display_name": "Diana Ross",
      "title": "CEO",
      "level": 3
    }
  ]
}
```

**Latency**: 100-150ms

---

#### `workday.hcm.update_employee`

Updates employee record fields. Triggers audit log.

**Request**:
```json
{
  "employee_id": "EMP001",
  "updates": {
    "job": {
      "title": "Staff Engineer"
    },
    "phone": {
      "mobile": "+1-555-0199"
    }
  },
  "effective_date": "2026-02-01",
  "reason": "Promotion"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "transaction_id": "TXN-20260127-001",
  "status": "PENDING_APPROVAL",
  "effective_date": "2026-02-01",
  "changes": [
    {
      "field": "job.title",
      "old_value": "Senior Engineer",
      "new_value": "Staff Engineer"
    }
  ]
}
```

**Latency**: 200-400ms (write operation)

---

#### `workday.hcm.terminate_employee`

Initiates employee termination workflow.

**Request**:
```json
{
  "employee_id": "EMP001",
  "termination_date": "2026-03-15",
  "reason_code": "VOLUNTARY_RESIGNATION",
  "notes": "Accepted position elsewhere"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "transaction_id": "TXN-20260127-002",
  "status": "PENDING_APPROVAL",
  "termination_date": "2026-03-15",
  "offboarding_flow_id": "FLOW-OFF-001"
}
```

**Latency**: 300-500ms

---

### Time Tracking Operations

#### `workday.time.get_balance`

Returns time off balances for an employee.

**Request**:
```json
{
  "employee_id": "EMP001",
  "as_of_date": "2026-01-27"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "as_of_date": "2026-01-27",
  "balances": [
    {
      "type": "PTO",
      "type_name": "Paid Time Off",
      "available_hours": 120,
      "used_hours": 40,
      "pending_hours": 8,
      "accrual_rate_per_period": 6.67,
      "max_carryover": 40
    },
    {
      "type": "SICK",
      "type_name": "Sick Leave",
      "available_hours": 48,
      "used_hours": 16,
      "pending_hours": 0,
      "accrual_rate_per_period": 4,
      "max_carryover": 80
    }
  ]
}
```

**Latency**: 50-100ms

---

#### `workday.time.list_requests`

Lists time off requests for an employee or team.

**Request**:
```json
{
  "employee_id": "EMP001",
  "status_filter": ["PENDING", "APPROVED"],
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-12-31"
  }
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "requests": [
    {
      "request_id": "TOR-001",
      "type": "PTO",
      "status": "APPROVED",
      "start_date": "2026-02-10",
      "end_date": "2026-02-14",
      "hours": 40,
      "submitted_at": "2026-01-15T10:30:00Z",
      "approved_by": "EMP042",
      "approved_at": "2026-01-16T09:00:00Z"
    },
    {
      "request_id": "TOR-002",
      "type": "PTO",
      "status": "PENDING",
      "start_date": "2026-04-20",
      "end_date": "2026-04-22",
      "hours": 24,
      "submitted_at": "2026-01-25T14:00:00Z",
      "approved_by": null,
      "approved_at": null
    }
  ],
  "count": 2
}
```

**Latency**: 100-150ms

---

#### `workday.time.get_request`

Gets details of a specific time off request.

**Request**:
```json
{
  "request_id": "TOR-001"
}
```

**Response**:
```json
{
  "request_id": "TOR-001",
  "employee_id": "EMP001",
  "employee_name": "Alice Johnson",
  "type": "PTO",
  "type_name": "Paid Time Off",
  "status": "APPROVED",
  "start_date": "2026-02-10",
  "end_date": "2026-02-14",
  "hours": 40,
  "notes": "Family vacation",
  "submitted_at": "2026-01-15T10:30:00Z",
  "approved_by": {
    "employee_id": "EMP042",
    "display_name": "Bob Martinez"
  },
  "approved_at": "2026-01-16T09:00:00Z",
  "history": [
    {
      "action": "SUBMITTED",
      "timestamp": "2026-01-15T10:30:00Z",
      "actor": "EMP001"
    },
    {
      "action": "APPROVED",
      "timestamp": "2026-01-16T09:00:00Z",
      "actor": "EMP042"
    }
  ]
}
```

**Latency**: 50-100ms

---

#### `workday.time.request`

Submits a new time off request.

**Request**:
```json
{
  "employee_id": "EMP001",
  "type": "PTO",
  "start_date": "2026-05-01",
  "end_date": "2026-05-02",
  "hours": 16,
  "notes": "Personal day"
}
```

**Response**:
```json
{
  "request_id": "TOR-003",
  "status": "PENDING",
  "submitted_at": "2026-01-27T15:00:00Z",
  "approver": {
    "employee_id": "EMP042",
    "display_name": "Bob Martinez"
  },
  "estimated_balance_after": 104
}
```

**Latency**: 150-250ms

---

#### `workday.time.approve`

Approves a pending time off request. Requires manager relationship.

**Request**:
```json
{
  "request_id": "TOR-002",
  "approver_id": "EMP042",
  "comments": "Approved - enjoy your time off"
}
```

**Response**:
```json
{
  "request_id": "TOR-002",
  "status": "APPROVED",
  "approved_at": "2026-01-27T16:00:00Z",
  "approved_by": "EMP042"
}
```

**Authorization Check**: Approver must be in employee's manager chain.

**Latency**: 200-300ms

---

#### `workday.time.cancel`

Cancels a time off request. Only owner or admin can cancel.

**Request**:
```json
{
  "request_id": "TOR-002",
  "reason": "Plans changed"
}
```

**Response**:
```json
{
  "request_id": "TOR-002",
  "status": "CANCELLED",
  "cancelled_at": "2026-01-27T17:00:00Z",
  "cancelled_by": "EMP001",
  "hours_restored": 24
}
```

**Latency**: 150-250ms

---

### Payroll Operations

#### `workday.payroll.get_compensation`

Returns current compensation details. Highly sensitive.

**Request**:
```json
{
  "employee_id": "EMP001"
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "compensation": {
    "base_salary": {
      "amount": 185000,
      "currency": "USD",
      "frequency": "ANNUAL"
    },
    "bonus_target": {
      "percentage": 15,
      "amount": 27750
    },
    "equity": {
      "grant_value": 50000,
      "vesting_schedule": "4 years with 1 year cliff"
    },
    "total_compensation": 262750
  },
  "pay_grade": "L5",
  "effective_date": "2025-01-01",
  "next_review_date": "2026-01-01"
}
```

**Audit**: Always VERBOSE  
**Latency**: 100-150ms

---

#### `workday.payroll.get_pay_statement`

Returns a specific pay statement.

**Request**:
```json
{
  "employee_id": "EMP001",
  "statement_id": "PAY-2026-01"
}
```

**Response**:
```json
{
  "statement_id": "PAY-2026-01",
  "employee_id": "EMP001",
  "pay_period": {
    "start": "2026-01-01",
    "end": "2026-01-15"
  },
  "pay_date": "2026-01-20",
  "earnings": {
    "regular": 7115.38,
    "overtime": 0,
    "bonus": 0,
    "gross": 7115.38
  },
  "deductions": {
    "federal_tax": 1423.08,
    "state_tax": 640.38,
    "social_security": 441.15,
    "medicare": 103.17,
    "health_insurance": 250.00,
    "retirement_401k": 711.54,
    "total": 3569.32
  },
  "net_pay": 3546.06,
  "ytd": {
    "gross": 7115.38,
    "taxes": 2607.78,
    "net": 3546.06
  }
}
```

**Latency**: 100-150ms

---

#### `workday.payroll.list_pay_statements`

Lists pay statements for an employee.

**Request**:
```json
{
  "employee_id": "EMP001",
  "year": 2026
}
```

**Response**:
```json
{
  "employee_id": "EMP001",
  "year": 2026,
  "statements": [
    {
      "statement_id": "PAY-2026-01",
      "pay_date": "2026-01-20",
      "gross": 7115.38,
      "net": 3546.06
    }
  ],
  "count": 1
}
```

**Latency**: 100-150ms

---

## Error Taxonomy

All errors follow a consistent structure:

```json
{
  "error_code": "EMPLOYEE_NOT_FOUND",
  "message": "Employee with ID 'EMP999' not found",
  "details": {
    "employee_id": "EMP999"
  },
  "retry_allowed": false
}
```

### Error Codes

| Code | HTTP Status | Retryable | Description |
|------|-------------|-----------|-------------|
| `EMPLOYEE_NOT_FOUND` | 404 | No | Employee ID does not exist |
| `REQUEST_NOT_FOUND` | 404 | No | Time off request not found |
| `STATEMENT_NOT_FOUND` | 404 | No | Pay statement not found |
| `INSUFFICIENT_BALANCE` | 400 | No | Not enough time off balance |
| `INVALID_DATE_RANGE` | 400 | No | Start date after end date |
| `INVALID_APPROVER` | 403 | No | Approver not in manager chain |
| `ALREADY_PROCESSED` | 409 | No | Request already approved/cancelled |
| `CONNECTOR_TIMEOUT` | 504 | Yes | Workday API timeout |
| `CONNECTOR_UNAVAILABLE` | 503 | Yes | Workday API down |
| `RATE_LIMITED` | 429 | Yes | Too many requests |

---

## Simulation Configuration

The simulated connector accepts configuration for testing scenarios:

```python
@dataclass
class WorkdaySimulationConfig:
    # Latency simulation
    base_latency_ms: int = 50
    latency_variance_ms: int = 50
    write_latency_multiplier: float = 3.0
    
    # Failure injection
    failure_rate: float = 0.0  # 0-1, percentage of requests that fail
    timeout_rate: float = 0.0  # 0-1, percentage that timeout
    
    # Data
    fixture_path: str = "fixtures/workday/"
    
    # Feature flags
    enforce_manager_chain: bool = True  # For approve operations
    enforce_balance_check: bool = True  # For time off requests

    # Concurrency
    # Mode: single-threaded asyncio (atomic dictionary updates, no locks required)
    concurrency_mode: str = "asyncio"
```

---

## Policy Extensions

Add these capabilities to `schemas/policy-schema.json`:

```yaml
capability_groups:
  workday_hcm_read:
    - "workday.hcm.get_employee"
    - "workday.hcm.list_direct_reports"
    - "workday.hcm.get_org_chart"
    - "workday.hcm.get_manager_chain"
    
  workday_hcm_full:
    - "workday.hcm.*"
    
  workday_time_read:
    - "workday.time.get_balance"
    - "workday.time.list_requests"
    - "workday.time.get_request"
    
  workday_time_write:
    - "workday.time.request"
    - "workday.time.approve"
    - "workday.time.cancel"
    
  workday_payroll_read:
    - "workday.payroll.get_compensation"
    - "workday.payroll.get_pay_statement"
    - "workday.payroll.list_pay_statements"
```

### Recommended Role Mappings

| Role | Capabilities | Use Case |
|------|-------------|----------|
| Employee Self-Service | `workday_hcm_read`, `workday_time_read`, `workday.time.request`, `workday.time.cancel` | Employees viewing own data |
| Manager | Above + `workday.time.approve`, `workday.hcm.list_direct_reports` | Team management |
| HR Admin | `workday_hcm_full`, `workday_time_*` | HR operations |
| HR Admin + Payroll | Above + `workday_payroll_read` | Full HR access |
| AI Assistant | `workday_hcm_read`, `workday_time_read` | Read-only lookups |
| Onboarding Workflow | `workday.hcm.get_employee`, `workday.hcm.update_employee` | Automated workflows |

---

## Backstage Readiness (Deferred)

When ready for Backstage integration, the connector will need:

1. **catalog-info.yaml**: Component registration with:
   - `spec.type: service`
   - `spec.lifecycle: production`
   - `spec.owner: hr-platform-team`
   - Annotations for API docs, PagerDuty, etc.

2. **API entity**: Link to OpenAPI spec for API catalog

3. **TechDocs**: Markdown docs for this spec

4. **Software Template**: Scaffolder template for creating new connectors following this pattern

---

## Implementation Checklist

- [ ] Port interface (`WorkdayConnectorPort`)
- [ ] Data models (Pydantic schemas for all request/response)
- [ ] Fixture loader (YAML/JSON employee data)
- [ ] Simulated adapter with latency
- [ ] Operation implementations (17 total)
- [ ] Error handling
- [ ] Policy YAML updates
- [ ] Unit tests
- [ ] Integration tests with auth
