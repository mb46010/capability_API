# Data Model: MCP Token Exchange

## Entities

### 1. Exchanged Token (JWT)

A short-lived JWT issued to the MCP Server acting on behalf of a user.

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `sub` | string | User Subject (e.g., "user@example.com") | Copied from Subject Token |
| `aud` | string | Audience | Configured |
| `iss` | string | Issuer | Configured |
| `exp` | int | Expiration Timestamp | `iat` + 300 (5 min) |
| `iat` | int | Issue Timestamp | Current Time |
| `scope` | list[str] | Scopes | `["mcp:use"]` |
| `acting_as` | string | Actor Indicator | Fixed: `"mcp-server"` |
| `original_token_id`| string | Provenance Link | `jti` of Subject Token |
| `auth_time` | int | Original Authentication Time | Copied from Subject Token (or `iat` if missing) |

### 2. Policy Conditions (Configuration)

Extensions to the existing Policy Engine configuration schema.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `required_scope` | string | No | If present, token MUST have this scope. |
| `max_auth_age_seconds`| int | No | If present, `auth_age` must be <= this value. |

## JSON Schema Changes

### Policy Schema (`config/policy-schema.json`)

```json
{
  "properties": {
    "conditions": {
      "properties": {
        "required_scope": {
          "type": "string",
          "description": "Scope required to access this capability (e.g., 'mcp:use')"
        },
        "max_auth_age_seconds": {
          "type": "integer",
          "description": "Maximum allowed age of authentication in seconds"
        }
      }
    }
  }
}
```
