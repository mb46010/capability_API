# Implementation Plan: Workday Actions

**Branch**: `004-workday-actions` | **Date**: 2026-01-28 | **Spec**: [specs/004-workday-actions/spec.md](specs/004-workday-actions/spec.md)
**Input**: Feature specification from `/specs/004-workday-actions/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a set of atomic, policy-governed HR actions (e.g., `get_employee`, `request_time_off`, `approve`) backed by the Workday Simulator. These actions must be OIDC-secured, audited, and strictly synchronous (< 1s), serving as the foundation for the "Action" layer of the Capability API.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, Pydantic V2, Authlib (for OIDC)
**Storage**: In-memory (Workday Simulator) with YAML fixtures for persistence
**Testing**: pytest (Unit + Integration)
**Target Platform**: Linux (Containerized)
**Project Type**: Web API (FastAPI)
**Performance Goals**: Actions must complete in < 1s (p99)
**Constraints**: Must work locally with Simulator; Strict OIDC enforcement; PII redaction in logs.
**Scale/Scope**: ~9 initial actions across HCM, Time, and Payroll domains.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: Uses `ConnectorPort` and `WorkdaySimulator` adapter.
- [x] **Actions vs Flows**: All proposed actions are synchronous and short-lived.
- [x] **Python-Native**: Logic implemented in Python services (`hcm`, `time`, `payroll`).
- [x] **Observability**: `Provenance` model defined; requires implementation of audit logging.
- [x] **Privacy & PII**: `update_contact_info` requires PII redaction in audit logs.
- [x] **Local Parity**: Simulator provides full functional parity locally.

## Project Structure

### Documentation (this feature)

```text
specs/004-workday-actions/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── api/
│   └── routes/
│       └── actions.py         # Main entry point for action execution
├── adapters/
│   ├── auth/                  # OIDC/Mock Auth
│   └── workday/
│       ├── client.py          # Simulator Dispatcher
│       ├── services/          # Domain Logic
│       │   ├── hcm.py         # get_employee, list_direct_reports, update_contact_info
│       │   ├── time.py        # get_balance, request, cancel, approve
│       │   └── payroll.py     # get_compensation
│       └── fixtures/          # YAML data
└── domain/
    ├── entities/
    │   └── action.py          # Action/Provenance models
    └── services/
        └── policy_engine.py   # Policy enforcement logic
```

**Structure Decision**: Option 1: Single project (Default)

## Authorization Implementation Strategy

The "Who can invoke" rules from the spec will be enforced via two layers:

1.  **Policy Engine (`policy-workday.yaml`)**:
    - **Agents**: Explicitly DENY `update_contact_info`, `get_compensation`, `approve` (by omission).
    - **Agents**: ALLOW `get_employee` (but Subject to field filtering), `get_balance`.
    - **Managers**: ALLOW `approve`, `list_direct_reports` (base permission).
    - **MFA Requirement**: `get_compensation` and `update_contact_info` must require `mfa_verified: true`.

2.  **Code-Level Enforcement (Service Layer)**:
    - **Field Filtering**: `get_employee` returns restricted fields for `AI_AGENT` principals (existing pattern).
    - **Own Data**: Check `principal.id == target.employee_id` for self-service actions.
    - **Manager Relationship**: Check `hcm.is_manager(principal.id, target.employee_id)` for `approve`/`list_direct_reports`.

## Development & Testing Strategy (Constitution Enforced)

1.  **Test-First (Article IV)**:
    - Create test files *before* implementation:
        - `tests/unit/adapters/workday/services/test_hcm_actions.py`
        - `tests/unit/adapters/workday/services/test_time_actions.py`
        - `tests/unit/adapters/workday/services/test_payroll_actions.py`
    - Define failing test cases for:
        - Happy path (e.g., `request_time_off` creates record).
        - Edge cases (e.g., negative balance, invalid dates).
        - Security (e.g., employee updating another's contact info -> 403).
    - Implement logic only after tests are defined.

2.  **Documentation as Code (Article VI)**:
    - Update `src/adapters/workday/README.ai.md`: Add new action capabilities and Pydantic schemas.
    - Update `src/domain/entities/README.ai.md`: Document the `ActionRequest`/`ActionResponse` structures.
    - Ensure all Pydantic models in `data-model.md` have `Field(description=...)`.

3.  **Logging & Privacy (Article VIII)**:
    - Replace any `print()` statements in `WorkdaySimulator` with standard `logging`.
    - Implement a `JSONLLogger` adapter that performs PII redaction (masking phone/salary/email values) before writing to `logs/audit.jsonl`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |