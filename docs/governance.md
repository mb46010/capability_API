# Governance Framework

The HR AI Platform implements a comprehensive governance framework to ensure secure, compliant, and auditable AI-to-Workday operations.

## Overview

Our governance model is built on three pillars:

1. **Policy-Driven Access Control**: All capability access is governed by explicit YAML policies that define who can do what, under which conditions.
2. **Continuous Verification**: Automated security testing ensures policies behave as intended across all scenarios.
3. **Audit Transparency**: Every action generates immutable audit logs with full provenance tracking.

## Key Resources

### Policy Verification Dashboard
The [Policy Verification Dashboard](policy-verification/latest.md) provides real-time visibility into our security posture. It includes:
- Pass/fail metrics for all policy scenarios
- Detailed test results with execution times
- Timestamp and policy version tracking
- Coverage across Admin, Employee, AI Agent, and HR Staff personas

This dashboard is automatically regenerated on every policy change to ensure stakeholders always see the current state.

### Policy Schema & Rules
Our [Policy Schema documentation](policy_schema.md) defines the authoritative access control model:
- Allow-list only approach (deny by default)
- Principal resolution order (specific > group > type)
- Wildcard matching semantics
- Condition evaluation logic

### Security Architecture
The [Security Architecture](security_architecture.md) document explains our defense-in-depth strategy:
- Layer 1: Centralized Policy Engine & MCP Gateway
- Layer 2: Service-Level Validation
- Layer 3: Data Filtering & PII Protection

## Compliance & Auditing

### Access Control Principles
1. **Least Privilege**: Principals only receive the minimum capabilities needed for their role
2. **Multi-Factor Authentication**: High-sensitivity operations (compensation, personal data updates) require MFA
3. **Environment Isolation**: Dev grants never apply in production
4. **Explicit Grants**: No implicit permissions or default-allow rules

### Audit Trail
Every capability invocation is logged with:
- Principal identity (subject/group/type)
- Capability identifier
- UTC timestamp
- Matched policy name
- Request/response metadata (with PII redacted)

### Continuous Testing
Changes to `config/policy-workday.yaml` must pass the verification suite before deployment:
```bash
./scripts/verify-policy run
```

New capabilities or roles require corresponding test scenarios in `tests/policy/scenarios/`.

## Governance Visibility in Backstage

The Backstage integration provides a read-only governance lens:
- **Capability Catalog**: Browse all actions and flows with sensitivity labels
- **Policy Verification**: View security test results
- **Entity Relationships**: See which policies govern each capability

See the [Backstage Integration Guide](backstage.md) for setup details.

## For Developers

- **[API Usage Guide](api_usage.md)**: How to invoke capabilities with proper authentication
- **[Onboarding Guide](onboarding.md)**: Getting started as a developer or consumer
- **[Troubleshooting](troubleshooting.md)**: Common issues and solutions

## For Compliance Officers

- Navigate to the [Policy Verification Dashboard](policy-verification/latest.md) to review current security test results
- Review the [Security Architecture](security_architecture.md) for defense-in-depth controls
- Check the [Policy Schema](policy_schema.md) for access control rules

---

**Last Updated**: Auto-generated from Git repository
**Policy Verification**: [View Latest Results](policy-verification/latest.md)
