# Troubleshooting Guide

Common issues encountered when working with the Capability API.

## Authentication & Authorization

### 1. Token Expired (`token_expired`)
- **Cause**: The mock JWT token has reached its `exp` time.
- **Solution**: Issue a new token using the `MockOktaProvider.issue_token()` method in your test or script. AI Agents have a default TTL of 300 seconds.

### 2. Access Denied (`FORBIDDEN`)
- **Cause**: The principal does not have the required capability in the current environment.
- **Solution**:
    - Check `config/policy-workday.yaml` to ensure the principal/group is mapped to the capability.
    - Verify that MFA is present in the token if the policy requires it (`amr: ["mfa"]`).
    - Ensure the `ENVIRONMENT` env var matches the policy environment.

## Connector Issues

### 1. Employee Not Found (`EMPLOYEE_NOT_FOUND`)
- **Cause**: The requested employee ID does not exist in the YAML fixtures.
- **Solution**: Verify the ID in `src/adapters/workday/fixtures/employees.yaml`. Use `/actions/test/reload-fixtures` if you just added it.

### 2. Connector Timeout (`CONNECTOR_TIMEOUT`)
- **Cause**: Failure injection is enabled or the base latency is set too high.
- **Solution**: Check `WorkdaySimulationConfig` in your dependency injection or environment variables.

## Development Tools

### 1. Pydantic Metadata Errors
- **Cause**: A new model field was added without a `Field(description="...")`.
- **Solution**: Run `pytest tests/unit/test_documentation_metadata.py` to identify missing descriptions and add them.

### 2. Spec/Task Desync
- **Cause**: The code has diverged from the `tasks.md` or `spec.md`.
- **Solution**: Re-run `/speckit.analyze` to detect inconsistencies and update documentation accordingly.
