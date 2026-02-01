# Developer Guide: Capability Registry

## Overview
The Capability Registry is the central source of truth for all HR Platform capabilities (Actions and Flows). It ensures consistency between policy definitions, implementation logic, and runtime execution.

## File Structure
Registry definitions are stored in a single YAML file:
`config/capabilities/index.yaml`

### Example Entry
```yaml
- id: "workday.hcm.get_employee"
  name: "Get Employee Profile"
  domain: "workday.hcm"
  type: "action"
  sensitivity: "medium"
  tags: ["read-only", "hcm", "pii"]
  description: "Retrieve basic public profile information for an employee"
```

## Adding a New Capability

### 1. Update the Registry
Add the capability to `config/capabilities/index.yaml`. Ensure the `id` follows the pattern `domain.subdomain.action`.

### 2. Validate Changes
Run the CLI tool to ensure the registry is still valid:
```bash
./scripts/capability-registry validate
```

### 3. Update Policy
Grant permissions to the new capability in `config/policy-workday.yaml`. You can reference the full ID or use wildcards (e.g., `workday.hcm.*`).

### 4. Cross-Validate Policy
Ensure the policy correctly references existing capabilities:
```bash
./scripts/capability-registry check-policy config/policy-workday.yaml
```

## Runtime Behavior
- **Startup**: The system cross-validates all policy files against the registry. If a policy references a non-existent capability, the application will fail to start.
- **Execution**: `ActionService` validates every request against the registry.
- **Subdomain Expansion**: If a domain is provided without a subdomain (e.g., `workday.get_employee`), the system dynamically derives available subdomains from the registry to find the canonical match (e.g., `workday.hcm.get_employee`).
- **Deprecation**: If a capability is marked as `deprecated: true`, it will still execute, but a warning will be logged.


## CLI Reference
- `list`: List all capabilities with optional filtering by `--domain`, `--type`, or `--tag`.
- `validate`: Check the registry file for schema errors or duplicate IDs.
- `check-policy <file>`: Validate a policy file against the registry.
- `stats`: Show distribution of capabilities by domain and type.
