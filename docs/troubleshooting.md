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

### 3. Ambiguous Principal Warning
- **Symptom**: Startup log shows `WARNING: Policy '...' has inline principal with both type '...' and a specific binding.`
- **Cause**: A policy rule defines an inline principal that includes both a generic `type` (e.g., `AI_AGENT`) and a specific `okta_subject` or `okta_group`.
- **Impact**: The policy will ONLY match the specific binding. It will NOT act as a generic grant for all principals of that type.
- **Solution**: Decide if the policy is meant for one specific entity (remove `type`) or all entities of a type (remove `okta_subject`/`okta_group`).

### 4. Invalid or missing X-Test-Secret
- **Symptom**: `403 Forbidden` when calling `/auth/test/tokens` or `/auth/test/users`.
- **Cause**: The `X-Test-Secret` header is missing or does not match the `MOCK_OKTA_TEST_SECRET` configuration.
- **Solution**: Add `-H "X-Test-Secret: mock-okta-secret"` to your curl command, or check your `.env` file for the correct secret.

### 5. MCP Unauthorized: Invalid or malformed token
- **Symptom**: MCP tools return `ERROR: UNAUTHORIZED: Invalid or malformed token`.
- **Cause**: The MCP server now enforces full signature verification. Forged tokens (e.g., those signed with `HS256` and a static secret) are now rejected.
- **Solution**: Ensure your client is sending a valid token issued by the `MockOktaProvider` (local) or real Okta (prod).

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
