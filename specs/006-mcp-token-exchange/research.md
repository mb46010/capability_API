# Research: MCP Token Exchange

**Feature**: MCP Token Exchange (006)
**Date**: 2026-01-31

## Decisions

### 1. RFC 8693 Implementation Strategy

**Decision**: Implement the Token Exchange logic manually within the existing `MockOktaProvider` and its FastAPI wrapper.
**Rationale**: `MockOktaProvider` is a custom, lightweight mock for development. Introducing a full OIDC library like `Authlib` *server-side* just for this mock would add unnecessary complexity. Manual implementation allows us to strictly control the behavior (e.g., deterministic `jti`, specific failure modes) for testing.
**Alternatives Considered**:
- **Using Authlib server**: Would require refactoring the entire `MockOktaProvider` to use Authlib's `AuthorizationServer`. Too high effort for a mock.
- **Using a real Okta dev instance**: Violates "Local Parity" and "Offline Development" principles.

### 2. Token Caching in MCP Server

**Decision**: Implement in-memory caching for exchanged tokens in the `MCP Server` using a simple dictionary with expiration checks.
**Rationale**: Avoids the dependency complexity of Redis/Memcached for this specific use case, as the MCP server is currently stateless/local.
**Alternatives Considered**:
- **No caching**: Rejected due to latency concerns (PRD requirement).
- **Redis**: Overkill for the current architecture scale.

### 3. Policy Schema Extension

**Decision**: Add `required_scope` (List[str] or str) and `max_auth_age_seconds` (int) to the `PolicyConditions` Pydantic model.
**Rationale**: Matches the PRD requirements and integrates naturally with the existing `PolicyEngine`.

## RFC 8693 Specification Summary

For reference during implementation:

**Request**:
- `grant_type`: `urn:ietf:params:oauth:grant-type:token-exchange`
- `subject_token`: The user's access token.
- `subject_token_type`: `urn:ietf:params:oauth:token-type:access_token`
- `requested_token_type`: `urn:ietf:params:oauth:token-type:access_token` (optional, default)
- `scope`: `mcp:use` (requested scope)

**Response**:
```json
{
  "access_token": "...",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
  "token_type": "Bearer",
  "expires_in": 300,
  "scope": "mcp:use"
}
```

## Security Considerations

- **Nesting**: Must explicitly check `acting_as` claim in `subject_token` and reject if present.
- **Auth Time**: Must copy `auth_time` from subject token. If missing, use `iat`.
