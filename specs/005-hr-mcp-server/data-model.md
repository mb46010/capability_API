# Data Model: HR Platform MCP Server

This document defines the entities and data structures handled by the MCP server. Note that the MCP server is largely a protocol adapter; these models reflect the schemas expected by/returned from the Capability API.

## Core Entities

### Employee
Represents the profile information for a person in the HR system.

| Field | Type | Description | PII? |
|-------|------|-------------|------|
| `employee_id` | string | Unique identifier (e.g., EMP001) | No |
| `name` | object | `{first, last, display}` | Yes |
| `email` | string | Work or personal email | Yes |
| `phone` | string | Contact number | Yes |
| `job` | object | `{title, department, location}` | No |
| `manager` | object | `{employee_id, display_name}` | No |
| `status` | string | `ACTIVE`, `INACTIVE`, `ON_LEAVE` | No |

### TimeOffRequest
Represents a leave submission.

| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique identifier (e.g., TOR-abc123) |
| `employee_id` | string | ID of the requester |
| `type` | string | `PTO` or `SICK` |
| `start_date` | string | ISO date (YYYY-MM-DD) |
| `end_date` | string | ISO date (YYYY-MM-DD) |
| `hours` | float | Total hours requested |
| `status` | string | `PENDING`, `APPROVED`, `CANCELLED` |
| `approver_id` | string | ID of the manager responsible for approval |

### Compensation
Sensitive financial details for an employee.

| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | string | Unique identifier |
| `base_salary` | object | `{amount, currency, frequency}` |
| `bonus_target` | object | `{percentage, amount}` |
| `pay_grade` | string | e.g., L5, M1 |
| `effective_date` | string | ISO date |

## Enums & Constants

### Roles
- `ADMIN`: Full access to all tools and all employee data.
- `EMPLOYEE`: Access to own data and basic organizational info.
- `AI_AGENT`: Limited access; PII masked; Payroll tools forbidden.

### Leave Types
- `PTO`: Paid Time Off
- `SICK`: Sick Leave

## Validation Rules (MCP Layer)

1. **Employee ID**: Must match regex `^EMP\d{3,}$`.
2. **Dates**: Must be valid ISO-8601 strings.
3. **Hours**: Must be positive floats.
4. **Transaction IDs**: Required for all write actions to ensure idempotency.
