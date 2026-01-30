# Data Model: HR Platform MCP Server

This document defines the entities and data structures handled by the MCP server as it interacts with the Capability API.

## Core Entities

### Employee (HCM)
| Field | Type | Description | PII? |
|-------|------|-------------|------|
| `employee_id` | string | Unique identifier (e.g., EMP001) | No |
| `name` | object | `{first, last, display}` | Yes |
| `personal_email` | string | Personal contact email | Yes |
| `phone` | object | `{type, number}` | Yes |
| `job` | object | `{title, department, location}` | No |
| `manager` | object | `{employee_id, display_name}` | No |
| `status` | string | `ACTIVE`, `INACTIVE`, `ON_LEAVE` | No |

### TimeOffRequest (Time)
| Field | Type | Description |
|-------|------|-------------|
| `request_id` | string | Unique identifier (e.g., TOR-ABC123) |
| `employee_id` | string | ID of the requester |
| `type` | string | `PTO`, `SICK`, `PERSONAL` |
| `start_date` | string | ISO-8601 date |
| `end_date` | string | ISO-8601 date |
| `hours` | number | Total duration |
| `status` | string | `PENDING`, `APPROVED`, `CANCELLED` |

### Compensation (Payroll)
| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | string | Unique identifier |
| `base_salary` | object | `{amount, currency, frequency}` |
| `bonus_target` | object | `{percentage, amount}` |
| `total_compensation`| number | Calculated total |
| `pay_grade` | string | Organizational pay level |

## Auth Context (Session)
| Field | Type | Description |
|-------|------|-------------|
| `principal_id` | string | Extracted `sub` claim |
| `principal_type` | enum | `HUMAN`, `AI_AGENT`, `MACHINE` |
| `groups` | list | Extracted `groups` claim |
| `mfa_verified` | boolean | Presence of `amr: ["mfa"]` |

## Validation Rules
1. **Employee ID**: Must match `^EMP\d{3,}$`.
2. **Transaction ID**: Auto-generated UUID v4 if not provided by client for write actions.
3. **Dates**: Must be valid ISO-8601 strings.