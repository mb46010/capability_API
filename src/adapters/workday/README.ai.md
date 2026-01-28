# Workday Adapter Context

## Purpose
Provides a simulation of the Workday HRIS system for local development and testing. Exposes synchronous "Actions" for HCM, Time Tracking, and Payroll domains.

## Capabilities

### HCM Domain (`workday.hcm`)
- `get_employee(employee_id)`: Retrieve employee details (Subject to field filtering for Agents).
- `get_manager_chain(employee_id)`: Retrieve management hierarchy.
- `list_direct_reports(manager_id)`: List employees reporting to a manager.
- `update_contact_info(employee_id, updates)`: Update email/phone (Redacted in logs).

### Time Domain (`workday.time`)
- `get_balance(employee_id)`: Check PTO/Sick balances.
- `request(employee_id, type, dates)`: Submit time-off request.
- `cancel(request_id, reason)`: Cancel a pending/approved request.
- `approve(request_id, approver_id)`: Approve a request (Manager only).

### Payroll Domain (`workday.payroll`)
- `get_compensation(employee_id)`: View salary/bonus (High sensitivity, MFA required).

## Schemas
See `src/domain/entities/action.py` for full Pydantic models.