# Feature Spec: Workday Actions

**Status**: Draft
**Created**: 2026-01-28
**Context**: Build a policy-governed action execution platform where every HR operation goes through explicit, auditable capabilities with OIDC-based authorization.

## Clarifications

### Session 2026-01-28
- Q: How should specific PII values be handled in the persistent audit log? → A: Redact values (replace sensitive literals with `[REDACTED]` or `***`).
- Q: How should "Own Data Only" constraints be enforced? → A: Code-level enforcement (API endpoint checks `token.sub == payload.employee_id` for Human principals).
- Q: For manager-scoped actions, how strict is the relationship validation? → A: Direct Manager Only (Principal must be the immediate manager of the target employee).
- Q: How should MFA be verified in the local environment? → A: Token Claim Mock (Verify `amr: ["mfa"]` claim in OIDC token).

## Scope Boundaries

**IN SCOPE (Actions):**
- Fast operations (< 1 second)
- Synchronous request/response
- No human waits
- Examples: get_employee, request_time_off, check_balance

**OUT OF SCOPE (Flows):**
- Multi-step orchestration
- Human approval waits
- Operations taking minutes to weeks
- Examples: full onboarding, approval workflows with delays

**Clear Rule:** If it needs human interaction → it's a flow → defer to later

## Architecture Principles

1. **Action = the atomic unit** - Single operation, immediate response
2. **Identity-first** - Every action requires OIDC token (human/workflow/agent)
3. **Policy-governed** - Declarative YAML defines who can do what
4. **Uniformly callable** - Same action, any caller type
5. **Audit everything** - Who invoked what, when, with what result
6. **Local = production** - Same auth boundaries in dev and prod
7. **Workday-agnostic** - Can swap simulation for real integration later

## Implementation Strategy

1. Start with 3-5 simple actions (get_employee, get_balance, request_time_off).
2. Prove the execution model works end-to-end
3. Add more actions incrementally
4. Flows come later when we understand the patterns

## Action Requirements

### 1. Read-Only Query Actions
- `workday.hcm.get_employee` (Directory lookup)
- `workday.time.get_balance` (Check time-off balances)
- `workday.hcm.get_manager_chain` (Org transparency)

### 2. State-Mutating Actions (Immediate)
- `workday.time.request` (Submit time-off request)
- `workday.time.cancel` (Cancel pending request)
- `workday.hcm.update_contact_info` (Update contact info - PII)

### 3. Authorization-Sensitive Actions
- `workday.payroll.get_compensation` (View salary - Verbose audit, MFA implied)

### 4. Manager-Scoped Actions
- `workday.time.approve` (Approve pending request)

### 5. Aggregate/Reporting Actions
- `workday.hcm.list_direct_reports` (Manager view)

## Security & Compliance
- **PII actions**: Update contact info.
- **High Sensitivity**: Compensation data.
- **Audit**: All actions must be logged.
- **Audit Redaction**: Sensitive PII values in `update_contact_info` and `get_compensation` must be redacted (e.g., `***`) in logs; field names remain visible.
- **Authorization Enforcement**: For Human principals, API endpoints must validate that the target `employee_id` matches the authenticated principal's ID ("Own Data Only"), unless the principal has a specific override role (e.g., HR Admin).
- **Manager Relationship Enforcement**: Manager-scoped actions (`approve`, `list_direct_reports`) must verify that the principal is the **immediate manager** of the target employee(s) via the HCM data.
- **MFA Verification**: Sensitive actions requiring MFA (Compensation, PII updates) must verify the `amr: ["mfa"]` claim in the OIDC token. In local/simulation, the `MockTokenVerifier` must be configurable to issue/accept this claim.
