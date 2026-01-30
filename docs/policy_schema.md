# Policy Schema: HR AI Platform Access Control

The policy YAML is the authoritative statement of intended access for the HR AI Platform. It defines which principals can invoke which capabilities, under what conditions, and with what audit requirements.

## Design Principles

1.  **Allow-list only**: If a principal/capability pair isn't explicitly granted, access is denied.
2.  **Most-specific match wins**: When multiple policies could apply, the most specific (by principal ID > principal type > wildcard) takes precedence.
3.  **Environment isolation**: Policies are environment-scoped. A `dev` grant never applies in `prod`.
4.  **Audit by default**: All capability invocations are logged. The policy controls verbosity, not whether logging occurs.

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

### Condition Evaluation

All specified conditions must be satisfied (AND logic). If any condition fails, the policy does not apply and evaluation continues to the next matching policy.

## Implementation Requirements

For detailed JSON Schema and examples, refer to the source document in `src/adapters/auth/policy-schema.md`.
