# Research: Workday Actions

**Status**: Complete
**Date**: 2026-01-28

## Unknowns & Resolutions

### 1. Audit Log Persistence
**Question**: `ActionService` generates provenance but doesn't persist it. Where should audit logs go?
**Finding**: Current implementation only returns provenance in API response.
**Decision**: Implement a **JSONL File Logger** (`logs/audit.jsonl`).
**Rationale**:
- Simple for local dev/simulated env.
- JSONL is easily parseable by agents/tools.
- "Local = Production" principle: In prod, this file would be rotated/shipped by an agent (e.g., Fluentd), so the app just writing to a file/stream is correct.

### 2. Policy Gaps for Self-Service
**Question**: Can employees update their own contact info?
**Finding**: `policy-workday.yaml` has `workday_hcm_write` (update_employee) restricted to `hr_staff` + MFA. `employees` group only has read access.
**Decision**:
- Define new capability: `workday.hcm.update_contact_info`.
- Add to `employees` principal with `ALLOW` (Self-Service).
- Add specific policy rule `employee-contact-update` with `MFA` condition if possible (or just allow for now).

### 3. Action Implementation Status
**Question**: Which actions are already implemented in `WorkdaySimulator`?
**Finding**: `client.py` has dispatch logic but delegates to services.
- `hcm.py`: Likely empty or minimal.
- `time.py`: Likely empty or minimal.
- `payroll.py`: Likely empty or minimal.
**Decision**: Full implementation required for:
- `get_employee` (HCM)
- `get_balance` (Time)
- `request` (Time)
- `cancel` (Time)
- `approve` (Time)
- `get_manager_chain` (HCM)
- `list_direct_reports` (HCM)
- `update_contact_info` (HCM)
- `get_compensation` (Payroll)

## Technology Decisions

| Area | Choice | Rationale |
|------|--------|-----------|
| **Audit** | `logging` + JSONFormatter | Standard lib, zero dep, easy to ship. |
| **Auth** | `Authlib` (OIDC) + Mock | Matches existing `MockOktaProvider` for local sim. |
| **Validation** | Pydantic V2 | Already in use, strong schema enforcement. |
| **Persistence** | In-Memory + YAML | Existing Simulator pattern is sufficient for "Actions". |

## API Design Notes

- **URL Structure**: `POST /actions/{domain}/{action}` (already exists).
- **Payload**: `ActionRequest` with `parameters: Dict`.
- **Response**: `ActionResponse` with `data` and `meta` (provenance).
