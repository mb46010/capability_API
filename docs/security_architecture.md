# Security Architecture

## Defense in Depth Strategy

Our platform implements security at **three layers**:

### Layer 1: Centralized Policy Engine
- **What**: YAML-based policy file defines all access grants. See **[Policy Schema](policy_schema.md)** for details.
- **Why**: Single source of truth for auditing and compliance
- **Example**: AI agents cannot access `workday.payroll.*` capabilities

### Layer 2: Service-Level Validation
- **What**: Each business service validates its specific constraints
- **Why**: Context-aware checks (e.g., "managers can only approve their direct reports")
- **Example**: Time-off approval verifies manager relationship

### Layer 3: Data Filtering
- **What**: Response payloads are filtered based on principal type
- **Why**: Even if authorization succeeds, PII is removed for AI agents
- **Example**: AI agent sees employee name but not SSN

## Audit Trail

Every action generates a log entry with:
- Who performed the action (principal ID)
- What capability was invoked
- When it occurred (UTC timestamp)
- What policy granted access
- PII automatically redacted

## MFA Enforcement

High-sensitivity operations require Multi-Factor Authentication:
- ✓ Viewing compensation data
- ✓ Updating personal information
- ✓ Approving manager-level actions

Policy engine validates MFA claim in JWT token.

## Testing

Run security test suite:
```bash
pytest tests/security/ -v
```

View audit logs:
```bash
tail -f logs/audit.jsonl | jq .
```