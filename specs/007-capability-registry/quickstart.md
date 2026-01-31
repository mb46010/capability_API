# Quickstart: Capability Registry

## Overview
The Capability Registry is the single source of truth for all actions and flows in the HR Platform.

## 1. Adding a New Capability

1. Open `config/capabilities/index.yaml`.
2. Add a new entry under `capabilities`:

```yaml
- id: "workday.hcm.new_action"
  name: "My New Action"
  domain: "workday.hcm"
  type: "action"
  sensitivity: "low"
  tags: ["experimental"]
```

3. Validate the registry:
   ```bash
   ./scripts/capability-registry validate
   ```

## 2. Using the CLI

List all capabilities:
```bash
./scripts/capability-registry list
```

Filter by domain:
```bash
./scripts/capability-registry list --domain workday.payroll
```

Check a policy file against the registry:
```bash
./scripts/capability-registry check-policy config/policy-workday.yaml
```

## 3. Runtime Integration

The registry is loaded automatically at startup.
- If you reference a missing capability in code or policy, the server will fail to start.
- If a client requests a missing capability, they receive a 400 Bad Request.
- If a client requests a `deprecated: true` capability, they receive the response but a warning is logged.
