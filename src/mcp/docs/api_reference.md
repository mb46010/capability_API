# Tool Reference: HR MCP Server

This server exposes 11 core HR tools categorized by domain.

## HCM Domain (Human Capital Management)

| Tool Name | Parameters | Allowed Roles | Description |
|-----------|------------|---------------|-------------|
| `get_employee` | `employee_id` | ALL | Look up professional profile (PII filtered for Agents). |
| `get_manager_chain`| `employee_id` | ALL | Get reporting line hierarchy. |
| `get_org_chart` | `root_id`, `depth` | ALL | View organizational structure. |
| `list_direct_reports`| `manager_id` | ADMIN | List all subordinates for a manager. |
| `update_contact_info`| `employee_id`, `updates`| ALL | Update personal email/phone. |

## Time Domain (Time & Attendance)

| Tool Name | Parameters | Allowed Roles | Description |
|-----------|------------|---------------|-------------|
| `get_pto_balance` | `employee_id` | ALL | Check vacation and sick leave balances. |
| `request_time_off` | `employee_id`, `type`, `start_date`, `end_date`, `hours`, `transaction_id`? | EMPLOYEE, ADMIN | Submit a new request. Auto-generates TXN ID if missing. |
| `cancel_time_off` | `request_id`, `reason`? | EMPLOYEE, ADMIN | Cancel a pending or approved request. |
| `approve_time_off` | `request_id` | ADMIN | Approve a pending request. |

## Payroll Domain (Financials)

| Tool Name | Parameters | Allowed Roles | Description |
|-----------|------------|---------------|-------------|
| `get_compensation` | `employee_id` | ADMIN | View salary and bonus details. **REQUIRES MFA**. |
| `get_pay_statement`| `statement_id` | ADMIN | View detailed pay slip. **REQUIRES MFA**. |
| `list_pay_statements`| `employee_id`, `year`?| EMPLOYEE, ADMIN | List historical statements. **REQUIRES MFA**. |

## Request Metadata
All tools expect an OIDC token passed via the MCP transport metadata (headers).

**Header Example:**
```text
Authorization: Bearer <JWT_HERE>
X-Request-ID: <UUID_HERE>
```
