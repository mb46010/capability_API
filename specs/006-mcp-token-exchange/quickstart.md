# Quickstart: Testing Token Exchange

## Prerequisites

- Local Python environment setup
- `jq` installed (for the demo script)

## Running the Demo

1. **Start the Services**:
   Open two terminal tabs:
   ```bash
   # Tab 1: Capability API
   uvicorn src.main:app --port 8000
   
   # Tab 2: Mock Okta (if running standalone, otherwise API starts it)
   # (For this feature, MockOkta is embedded in the main app for dev, 
   # or run explicitly if needed. Assuming main app for now.)
   ```

2. **Run the Demonstration Script**:
   We have created a script `scripts/demo/token_exchange_demo.sh` (to be implemented).
   
   ```bash
   chmod +x scripts/demo/token_exchange_demo.sh
   ./scripts/demo/token_exchange_demo.sh
   ```

## Manual Verification Steps

### 1. Issue a User Token
```bash
USER_TOKEN=$(curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=password&username=user@local.test&password=any" | jq -r .access_token)
```

### 2. Exchange for MCP Token
```bash
curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=$USER_TOKEN" \
  -d "subject_token_type=urn:ietf:params:oauth:token-type:access_token" \
  -d "scope=mcp:use"
```
**Verify**:
- `expires_in` is ~300 (5 mins)
- `scope` contains `mcp:use`

### 3. Verify Direct Access Rejection
Try to use the **Exchanged Token** against the API directly:
```bash
curl -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer $MCP_TOKEN" \
  ...
```
**Expected**: `403 Forbidden` ("MCP-scoped tokens cannot be used for direct API access")
