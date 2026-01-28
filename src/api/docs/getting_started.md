# Getting Started with the API

## 1. Prerequisites
- Python 3.11+
- Dependencies installed: `pip install -r requirements.txt`

## 2. Running the Server
Start the API in development mode:
```bash
uvicorn src.main:app --reload
```
The API will be available at `http://localhost:8000`.
Swagger documentation is at `http://localhost:8000/docs`.

## 3. Simplified Testing with Scripts

To simplify testing, several helper scripts are provided in `scripts/api/`. These scripts handle token acquisition and JSON formatting automatically.

### A. Run a Smoke Test
Execute a suite of common scenarios (Agent lookup, User balance, MFA checks):
```bash
./scripts/api/smoke-test.sh
```

### B. Run a Specific Action
Execute any action for a specific persona:
```bash
# Usage: ./scripts/api/run-action.sh <persona> <domain> <action> '<params_json>'
./scripts/api/run-action.sh user workday.time get_balance '{"employee_id": "EMP001"}'
```
**Personas supported:** `admin`, `user`, `agent`, `mfa` (for sensitive data).

### C. Get a Raw Token
If you prefer using `curl` or Postman directly:
```bash
./scripts/api/get-token.sh agent
```

## 4. How to Get a Bearer Token (Manual Method)

The API is secured via OIDC. In local development, we use a `MockOktaProvider` that mimics real Okta behavior.

### Step 1: Identify your Persona
The permissions are tied to the `sub` (subject) claim in your token. Common subjects from the simulator fixtures:
- `admin@local.test`: Full access (Requires MFA for some actions).
- `user@local.test` (or `EMP001`): Standard employee access (Self-service only).
- `agent-assistant@local.test`: AI Agent access (Filtered fields).

### Step 2: Request the Token
You can obtain a valid JWT using `curl` against the mock token endpoint.

**Option A: Standard Password Grant**
```bash
curl -X POST http://localhost:8000/oauth2/default/v1/token \
  -d "grant_type=password" \
  -d "username=admin@local.test" \
  -d "password=any-password" \
  -d "scope=openid"
```
*Note: In mock mode, any password is accepted for registered users.*

**Option B: Create a Token with Specific Claims (MFA)**
For actions requiring MFA (like `get_compensation`), your token must include the `amr: ["mfa"]` claim. You can use the mock's admin endpoint to mint such a token:
```bash
curl -X POST http://localhost:8000/test/tokens \
  -H "Content-Type: application/json" \
  -d '{ "subject": "admin@local.test", "additional_claims": { "amr": ["mfa", "pwd"] } }'
```

### Step 3: Extract the `access_token`
Both methods return a JSON object. Copy the `access_token` string value.

### Step 4: Use the Token in your Request
Include the token in the `Authorization` header of your API calls:
```bash
curl -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer <YOUR_TOKEN_HERE>" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}'
```

## 4. Understanding Authentication Logic
For local development, the system validates the JWT signature against the mock provider's public key.
- **Own Data Only**: If you are logged in as `EMP001`, you can only view `EMP001`'s balance.
- **MFA Enforcement**: If an action is marked as high-sensitivity in `policy.yaml`, the token MUST have the `mfa` claim.

## 5. Adding New Routes
1.  Define the business logic in a domain service (`src/domain/services`).
2.  Add the route to the appropriate file in `src/api/routes/`.
3.  Register the new capability in `config/policy.yaml`.