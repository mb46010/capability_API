# API Usage Guide

## Getting Started

### 1. Running the Server
Start the API in development mode:
```bash
uvicorn src.main:app --reload
```
The API will be available at `http://localhost:8000`.
Swagger documentation is at `http://localhost:8000/docs`.

### 2. Authentication

The API is secured via OIDC. In local development, we use a `MockOktaProvider` that mimics real Okta behavior.

#### Identify your Persona
The permissions are tied to the `sub` (subject) claim in your token. Common subjects from the simulator fixtures:
- `admin@local.test`: Full access (Requires MFA for some actions).
- `user@local.test` (or `EMP001`): Standard employee access (Self-service only).
- `agent-assistant@local.test`: AI Agent access (Filtered fields).

#### Using Helper Scripts
To simplify testing, several helper scripts are provided in `scripts/api/`:
- `smoke-test.sh`: Runs a suite of common scenarios.
- `run-action.sh`: Executes a specific action for a persona.
- `get-token.sh`: Obtains a raw token for a persona.

## Standard Request Pattern

All actions follow a standard POST pattern to `/actions/{domain}/{action}`.

**Example Request:**
```bash
curl -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "X-Idempotency-Key: <UNIQUE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}'
```

### 3. Idempotency

For write operations (like `update`, `request`, `approve`), you should provide an `X-Idempotency-Key` header. 
- If the request succeeds, the result is cached for a configurable duration.
- Subsequent requests with the same key, action, and principal will return the cached result instead of re-executing the operation.
- The cache key is scoped to the `principal_id` and the `action` to prevent cross-user or cross-action collisions.

## Advanced Authentication (MFA)

For actions requiring MFA (like `get_compensation` or `approve` time-off), your token must include the `amr: ["mfa"]` claim. You can use the mock's admin endpoint to mint such a token (requires the test secret):

```bash
curl -X POST http://localhost:8000/auth/test/tokens \
  -H "Content-Type: application/json" \
  -H "X-Test-Secret: <YOUR_MOCK_OKTA_TEST_SECRET>" \
  -d '{ "subject": "admin@local.test", "additional_claims": { "amr": ["mfa", "pwd"] } }'
```
