# Workday Simulator Adapter

Provides a simulation of the Workday HRIS system for local development and testing. Exposes synchronous "Actions" for HCM, Time Tracking, and Payroll domains.

## Overview

The Workday Simulator is a critical component for development, allowing for safe, fast, and deterministic testing of HR capabilities.

- [Functional Documentation](workday_functional.md): Purpose, domains, and personas.
- [Technical Documentation](workday_technical.md): Architecture, state management, and simulation features.

## Capabilities

### HCM Domain (`workday.hcm`)
- `get_employee(employee_id)`: Retrieve employee details.
- `get_manager_chain(employee_id)`: Retrieve management hierarchy.
- `list_direct_reports(manager_id)`: List employees reporting to a manager.
- `update_contact_info(employee_id, updates)`: Update email/phone.

### Time Domain (`workday.time`)
- `get_balance(employee_id)`: Check PTO/Sick balances.
- `request(employee_id, type, dates)`: Submit time-off request.
- `cancel(request_id, reason)`: Cancel a pending/approved request.
- `approve(request_id, approver_id)`: Approve a request (Manager only).

### Payroll Domain (`workday.payroll`)
- `get_compensation(employee_id)`: View salary/bonus (High sensitivity, MFA required).

## Schemas
See `src/domain/entities/action.py` for full Pydantic models.
