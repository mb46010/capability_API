# Policy Schema: HR AI Platform Access Control

**Document**: `specs/001-capability-api/policy-schema.md`  
**Status**: Draft  
**Last Updated**: 2026-01-25

## Overview

The policy YAML is the authoritative statement of intended access for the HR AI Platform. It defines which principals can invoke which capabilities, under what conditions, and with what audit requirements.

This document specifies:
1. The JSON Schema for policy YAML validation
2. Semantics for policy evaluation
3. Realistic examples covering all principal types

---

## Design Principles

1. **Allow-list only**: If a principal/capability pair isn't explicitly granted, access is denied.
2. **Most-specific match wins**: When multiple policies could apply, the most specific (by principal ID > principal type > wildcard) takes precedence.
3. **Environment isolation**: Policies are environment-scoped. A `dev` grant never applies in `prod`.
4. **Audit by default**: All capability invocations are logged. The policy controls verbosity, not whether logging occurs.

---

## JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://hr-ai-platform.example.com/schemas/policy.json",
  "title": "HR AI Platform Access Policy",
  "description": "Defines access control rules mapping principals to capabilities",
  "type": "object",
  "required": ["version", "policies"],
  "additionalProperties": false,
  "properties": {
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+$",
      "description": "Schema version (e.g., '1.0')"
    },
    "metadata": {
      "type": "object",
      "properties": {
        "last_reviewed": {
          "type": "string",
          "format": "date",
          "description": "Date of last human review"
        },
        "reviewed_by": {
          "type": "string",
          "description": "Identity of reviewer"
        },
        "ticket": {
          "type": "string",
          "description": "Reference to approval ticket (e.g., JIRA-1234)"
        }
      }
    },
    "principals": {
      "type": "object",
      "description": "Named principal definitions for reuse",
      "additionalProperties": {
        "$ref": "#/$defs/principal_definition"
      }
    },
    "capability_groups": {
      "type": "object",
      "description": "Named groups of capabilities for reuse",
      "additionalProperties": {
        "type": "array",
        "items": { "type": "string" }
      }
    },
    "policies": {
      "type": "array",
      "items": { "$ref": "#/$defs/policy_rule" },
      "minItems": 1
    },
    "connector_constraints": {
      "type": "object",
      "description": "Reserved for future connector-level trust controls",
      "additionalProperties": true
    }
  },
  "$defs": {
    "principal_definition": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["HUMAN", "MACHINE", "AI_AGENT"]
        },
        "okta_subject": {
          "type": "string",
          "description": "Okta subject claim (for specific principal binding)"
        },
        "okta_group": {
          "type": "string",
          "description": "Okta group membership requirement"
        },
        "description": {
          "type": "string"
        },
        "provisioning_ticket": {
          "type": "string",
          "description": "Ticket reference for when this principal was provisioned"
        }
      }
    },
    "policy_rule": {
      "type": "object",
      "required": ["name", "principal", "capabilities", "environments", "effect"],
      "additionalProperties": false,
      "properties": {
        "name": {
          "type": "string",
          "description": "Human-readable policy name"
        },
        "description": {
          "type": "string"
        },
        "principal": {
          "oneOf": [
            { "type": "string", "description": "Reference to named principal or principal type" },
            { "$ref": "#/$defs/principal_definition" }
          ]
        },
        "capabilities": {
          "oneOf": [
            { "type": "array", "items": { "type": "string" } },
            { "type": "string", "description": "Reference to named capability group" }
          ]
        },
        "environments": {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["local", "dev", "staging", "prod"]
          },
          "minItems": 1
        },
        "effect": {
          "type": "string",
          "enum": ["ALLOW"],
          "description": "Currently only ALLOW is supported (deny-by-default)"
        },
        "conditions": {
          "type": "object",
          "properties": {
            "time_window": {
              "type": "object",
              "properties": {
                "start": { "type": "string", "pattern": "^\\d{2}:\\d{2}$" },
                "end": { "type": "string", "pattern": "^\\d{2}:\\d{2}$" },
                "timezone": { "type": "string" }
              }
            },
            "max_ttl_seconds": {
              "type": "integer",
              "minimum": 60,
              "description": "Maximum token TTL for this grant (primarily for AI_AGENT)"
            },
            "require_mfa": {
              "type": "boolean"
            },
            "ip_allowlist": {
              "type": "array",
              "items": { "type": "string" }
            }
          }
        },
        "audit": {
          "type": "string",
          "enum": ["BASIC", "VERBOSE"],
          "default": "BASIC",
          "description": "BASIC logs invocation metadata; VERBOSE includes input/output payloads"
        },
        "approval": {
          "type": "object",
          "description": "Metadata about when/why this policy was approved",
          "properties": {
            "approved_by": { "type": "string" },
            "approved_at": { "type": "string", "format": "date" },
            "ticket": { "type": "string" },
            "rationale": { "type": "string" }
          }
        }
      }
    }
  }
}
```

---

## Policy Evaluation Semantics

### Scope Matching

Capabilities use dot-notation namespacing: `{domain}.{operation}` or `{domain}.{subdomain}.{operation}`.

Matching rules:
- **Exact match**: `workday.get_employee` matches only that capability
- **Wildcard suffix**: `workday.*` matches all Workday capabilities
- **Full wildcard**: `*` matches everything (use with extreme caution)

### Principal Resolution Order

When evaluating access, policies are checked in this order (first match wins):

1. Policies matching the specific `okta_subject`
2. Policies matching the principal's `okta_group`
3. Policies matching the principal's `type` (HUMAN, MACHINE, AI_AGENT)
4. No match → DENY

### Environment Isolation

A policy only applies if the current runtime environment is in the policy's `environments` list. There is no inheritance or fallback between environments.

### Condition Evaluation

All specified conditions must be satisfied (AND logic). If any condition fails, the policy does not apply and evaluation continues to the next matching policy.

---

## Examples

### Example 1: Human Admin (Full Access)

```yaml
version: "1.0"

metadata:
  last_reviewed: "2026-01-15"
  reviewed_by: "platform-team@example.com"
  ticket: "HRAI-101"

principals:
  hr_platform_admins:
    type: HUMAN
    okta_group: "hr-platform-admins"
    description: "HR Platform administrators with full access"
    provisioning_ticket: "HRAI-042"

capability_groups:
  all_actions:
    - "workday.*"
    - "calendar.*"
    - "ticketing.*"
  all_flows:
    - "hr.onboarding"
    - "hr.offboarding"
    - "hr.role_change"
    - "hr.compensation_review"

policies:
  - name: "admin-full-access"
    description: "Platform admins can invoke any capability for debugging and support"
    principal: "hr_platform_admins"
    capabilities:
      - "workday.*"
      - "calendar.*"
      - "ticketing.*"
      - "hr.*"
    environments: ["local", "dev", "staging", "prod"]
    effect: ALLOW
    conditions:
      require_mfa: true
    audit: VERBOSE
    approval:
      approved_by: "ciso@example.com"
      approved_at: "2026-01-10"
      ticket: "SEC-2026-001"
      rationale: "Platform team requires full access for incident response and debugging"
```

### Example 2: Machine Workflow (Scoped to Specific Flow)

```yaml
version: "1.0"

principals:
  onboarding_workflow:
    type: MACHINE
    okta_subject: "svc-onboarding-workflow@example.com"
    description: "Service account for automated onboarding workflow"
    provisioning_ticket: "HRAI-078"

policies:
  - name: "onboarding-workflow-permissions"
    description: "Onboarding workflow can read employee data and trigger onboarding flow"
    principal: "onboarding_workflow"
    capabilities:
      - "workday.get_employee"
      - "workday.get_manager"
      - "calendar.check_availability"
      - "ticketing.create_ticket"
      - "hr.onboarding"  # Flow trigger
    environments: ["dev", "staging", "prod"]
    effect: ALLOW
    audit: BASIC
    approval:
      approved_by: "hr-engineering-lead@example.com"
      approved_at: "2026-01-08"
      ticket: "HRAI-078"
      rationale: "Required for automated onboarding pipeline"

  - name: "onboarding-workflow-local-dev"
    description: "Extended permissions for local development and testing"
    principal: "onboarding_workflow"
    capabilities:
      - "workday.*"
      - "calendar.*"
      - "ticketing.*"
      - "hr.onboarding"
    environments: ["local"]
    effect: ALLOW
    audit: VERBOSE
```

### Example 3: AI Agent (Limited Scope, Short TTL)

```yaml
version: "1.0"

principals:
  hr_assistant_agent:
    type: AI_AGENT
    okta_subject: "agent-hr-assistant@example.com"
    description: "Conversational AI agent for employee self-service queries"
    provisioning_ticket: "HRAI-112"

policies:
  - name: "hr-assistant-read-only"
    description: "AI assistant can only read non-sensitive employee data"
    principal: "hr_assistant_agent"
    capabilities:
      - "workday.get_employee"           # Read own profile
      - "workday.get_org_chart"          # Read org structure
      - "calendar.check_availability"    # Check meeting availability
      - "ticketing.get_ticket_status"    # Check ticket status
    environments: ["staging", "prod"]
    effect: ALLOW
    conditions:
      max_ttl_seconds: 300  # 5 minute token max
    audit: VERBOSE  # All AI agent actions logged in detail
    approval:
      approved_by: "security-review@example.com"
      approved_at: "2026-01-20"
      ticket: "SEC-2026-015"
      rationale: "Minimal read-only access for employee self-service. No write operations. No PII beyond basic directory info."

  - name: "hr-assistant-denied-capabilities"
    # Note: This is documentation only. Deny-by-default means unlisted capabilities are already denied.
    # Keeping this as a comment for clarity on intentional exclusions:
    #
    # EXPLICITLY DENIED:
    # - workday.get_compensation      # Sensitive PII
    # - workday.update_*              # No write access
    # - hr.*                          # No flow triggers
    # - ticketing.create_ticket       # No ticket creation
```

### Example 4: Cross-Environment Access (Staging Promotion)

```yaml
version: "1.0"

metadata:
  last_reviewed: "2026-01-22"
  reviewed_by: "release-engineering@example.com"
  ticket: "REL-2026-003"

principals:
  release_pipeline:
    type: MACHINE
    okta_subject: "svc-release-pipeline@example.com"
    description: "CI/CD pipeline for staging-to-prod promotion"
    provisioning_ticket: "HRAI-095"

  staging_testers:
    type: HUMAN
    okta_group: "staging-testers"
    description: "QA team members with staging access"
    provisioning_ticket: "HRAI-088"

policies:
  - name: "release-pipeline-staging"
    description: "Release pipeline can invoke all capabilities in staging for integration tests"
    principal: "release_pipeline"
    capabilities:
      - "*"  # Full access for integration testing
    environments: ["staging"]
    effect: ALLOW
    conditions:
      time_window:
        start: "06:00"
        end: "22:00"
        timezone: "America/Los_Angeles"
    audit: VERBOSE
    approval:
      approved_by: "platform-lead@example.com"
      approved_at: "2026-01-05"
      ticket: "HRAI-095"
      rationale: "Integration test suite requires full capability access"

  - name: "release-pipeline-prod-readonly"
    description: "Release pipeline can verify prod deployment but not modify"
    principal: "release_pipeline"
    capabilities:
      - "workday.get_employee"
      - "ticketing.get_ticket_status"
    environments: ["prod"]
    effect: ALLOW
    audit: BASIC
    approval:
      approved_by: "platform-lead@example.com"
      approved_at: "2026-01-05"
      ticket: "HRAI-095"
      rationale: "Smoke test verification only"

  - name: "staging-testers-full"
    description: "QA team has full access in staging for manual testing"
    principal: "staging_testers"
    capabilities:
      - "*"
    environments: ["staging"]
    effect: ALLOW
    conditions:
      require_mfa: true
    audit: VERBOSE
    approval:
      approved_by: "qa-lead@example.com"
      approved_at: "2026-01-12"
      ticket: "QA-2026-008"
      rationale: "Manual test execution requires full capability access"
```

---

## Mock Okta Requirements

For local development, the mock Okta implementation must support:

### Token Claims

```json
{
  "sub": "user@example.com",           // Maps to okta_subject
  "groups": ["hr-platform-admins"],    // Maps to okta_group
  "principal_type": "HUMAN",           // Custom claim: HUMAN | MACHINE | AI_AGENT
  "exp": 1737849600,                   // Expiration timestamp
  "iat": 1737846000,                   // Issued at
  "scope": "openid profile"            // Standard OIDC scopes (not used for capability auth)
}
```

### Mock Behaviors

1. **Token generation**: Issue tokens with configurable claims for each principal type
2. **TTL enforcement**: Respect `max_ttl_seconds` from policy conditions
3. **Group membership**: Support group claims for role-based policies
4. **MFA simulation**: When `require_mfa: true`, mock should require a flag/header indicating MFA was performed

### Test Principals (Pre-configured in Mock)

| Principal ID | Type | Groups | Purpose |
|--------------|------|--------|---------|
| `admin@local.test` | HUMAN | `hr-platform-admins` | Full admin testing |
| `user@local.test` | HUMAN | `employees` | Standard user testing |
| `svc-workflow@local.test` | MACHINE | — | Machine workflow testing |
| `agent-assistant@local.test` | AI_AGENT | — | AI agent testing |
| `unauthorized@local.test` | HUMAN | — | Negative testing (no grants) |

---

## Connector Constraints (Reserved)

This section is reserved for future connector-level trust controls. Anticipated needs:

```yaml
connector_constraints:
  workday:
    rate_limit:
      requests_per_minute: 100
      burst: 20
    timeout_seconds: 30
    circuit_breaker:
      failure_threshold: 5
      reset_timeout_seconds: 60
    allowed_operations:
      - "get_*"
      - "list_*"
    # credential_ref: "vault://hr-platform/workday-cdata"  # Future: external secret reference
```

This will be fleshed out once mock connectors are better defined.

---

## Validation and Enforcement

### Build-Time Validation

The policy YAML is validated against this schema in CI:
- Schema compliance
- No duplicate policy names
- Referenced principals and capability groups exist
- Environment values are valid

### Runtime Enforcement

The Capability API enforces policies at request time:

1. Extract principal identity from Okta token
2. Identify the requested capability from the endpoint
3. Load policies matching the principal (by subject → group → type)
4. Filter to policies matching current environment
5. Check if any matching policy grants the capability
6. Evaluate conditions (TTL, MFA, time window, IP)
7. ALLOW if all checks pass; DENY otherwise
8. Log according to policy's audit level

### Future: Drift Detection

When implemented, drift detection will compare:
- Principals defined in YAML vs. principals provisioned in Okta
- Capability grants in YAML vs. scopes assigned in Okta
- Report discrepancies via Backstage dashboard / alerts

---

## Change Management

All policy changes must:

1. Be submitted via PR to the `policy/` directory
2. Include an `approval` block with ticket reference
3. Pass schema validation in CI
4. Be reviewed by at least one platform team member
5. For `prod` environment grants: require security team approval

---

## Appendix: Capability Naming Conventions

| Domain | Example Capabilities | Notes |
|--------|---------------------|-------|
| `workday` | `workday.get_employee`, `workday.update_employee`, `workday.list_direct_reports` | HR system of record |
| `calendar` | `calendar.check_availability`, `calendar.create_event` | Scheduling integration |
| `ticketing` | `ticketing.create_ticket`, `ticketing.get_ticket_status`, `ticketing.update_ticket` | ServiceNow/Jira integration |
| `hr` | `hr.onboarding`, `hr.offboarding`, `hr.role_change` | Long-running flows (not actions) |

Flow capabilities (under `hr.*`) trigger long-running processes. Action capabilities (all others) are synchronous operations.
