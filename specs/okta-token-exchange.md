# Token Scoping & Authentication PRD (Improved)

**Version**: 2.0  
**Status**: Ready for Implementation  
**Owner**: HR AI Platform Security Team  
**Target**: Pre-Demo Hardening

---

## Executive Summary

**Problem**: MCP server currently uses full user tokens with 1-hour lifetime, creating excessive privilege scope if compromised.

**Solution**: Implement OAuth 2.0 Token Exchange (RFC 8693) to issue short-lived (5-min), scope-restricted tokens specifically for MCP operations, combined with step-up authentication for sensitive capabilities.

**Security Impact**:
- **Blast Radius**: 1 hour → 5 minutes (92% reduction)
- **Privilege Scope**: All user capabilities → MCP-only operations
- **Auditability**: Enhanced provenance tracking with token chain visibility

---

## Background & Context

### Current State (Insecure)

**Token Flow**:
```
User → Chainlit → Full User Token (1hr) → MCP Server → Capability API
```

**Security Gaps**:
1. **Excessive TTL**: MCP holds 1-hour tokens (AI agents get 5-min tokens, but MCP gets full human tokens)
2. **No Scope Restriction**: MCP token can be used for direct API access (bypassing MCP audit trail)
3. **No Provenance**: Audit logs don't distinguish "user via MCP" from "user direct"
4. **Token Reuse**: Same token used across multiple contexts (Chainlit UI + MCP server)

**Attack Scenario**:
```
1. MCP server compromised
2. Attacker extracts token from memory
3. Token valid for 60 minutes
4. Attacker calls API directly (bypassing MCP audit)
5. No indication in logs that MCP was compromised
```

---

### Target State (Secure)

**Token Flow**:
```
User → Chainlit → User Token (1hr)
                    ↓
            Token Exchange (MockOkta)
                    ↓
            MCP-Scoped Token (5min) → MCP Server → Capability API
```

**Security Properties**:
1. **Temporal Isolation**: 5-minute blast radius
2. **Scope Isolation**: Token only valid for MCP operations (not direct API)
3. **Provenance Chain**: Audit trail shows `acting_through: mcp-server`
4. **Freshness Enforcement**: Sensitive ops require recent (<5min) MFA

---

## Requirements

### FR-001: OAuth 2.0 Token Exchange (RFC 8693)

**Specification**: MockOkta must support token exchange endpoint.

**Endpoint**: `POST /oauth2/v1/token`

**Request**:
```http
POST /oauth2/v1/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=<USER_TOKEN>
&subject_token_type=urn:ietf:params:oauth:token-type:access_token
&requested_token_type=urn:ietf:params:oauth:token-type:access_token
&scope=mcp:use
&audience=api://hr-ai-platform
```

**Response**:
```json
{
  "access_token": "<MCP_SCOPED_TOKEN>",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
  "token_type": "Bearer",
  "expires_in": 300,
  "scope": "mcp:use"
}
```

**Token Claims (Exchanged)**:
```json
{
  "sub": "EMP001",
  "principal_type": "HUMAN",
  "groups": ["employees"],
  "amr": ["mfa", "pwd"],
  "auth_time": 1706445600,              // ← Preserved from original
  "iat": 1706445660,                    // ← NEW issue time
  "exp": 1706445960,                    // ← 5 minutes from iat
  "scope": ["mcp:use"],                 // ← NEW: restricted scope
  "acting_as": "mcp-server",            // ← NEW: provenance marker
  "original_token_id": "uuid-...",      // ← NEW: links to parent token
  "aud": "api://hr-ai-platform",
  "iss": "http://localhost:9000/oauth2/default"
}
```

**Validation Rules**:
1. `subject_token` MUST be a valid, non-expired user token
2. `auth_time` claim MUST be copied from original token
3. `scope` MUST be restricted to requested value (default: `mcp:use`)
4. TTL MUST be ≤ 300 seconds (5 minutes)
5. `original_token_id` MUST reference parent token's `jti`

**Acceptance Criteria**:
- ✅ MockOkta accepts RFC 8693 exchange requests
- ✅ Exchanged token has 5-minute TTL
- ✅ `auth_time` preserved from original token
- ✅ `scope` claim includes only `mcp:use`
- ✅ `acting_as` claim present for audit

---

### FR-002: Scope-Based Authorization

**Specification**: Policy engine must enforce scope requirements.

**Policy Schema Extension**:
```yaml
# config/policy-workday.yaml
policies:
  - name: "mcp-server-direct-access-denied"
    principal: "mcp_users"
    capabilities: ["*"]
    environments: ["local", "dev", "prod"]
    effect: "ALLOW"
    conditions:
      required_scope: "mcp:use"        # ← NEW
      require_mfa: false
```

**Enforcement Logic**:
```python
# src/domain/services/policy_engine.py
def _evaluate_conditions(self, rule, token_claims, ...):
    # Existing checks (MFA, TTL, IP)...
    
    # NEW: Scope validation
    if rule.conditions and rule.conditions.required_scope:
        token_scopes = token_claims.get("scope", [])
        if rule.conditions.required_scope not in token_scopes:
            logger.warning(f"Scope mismatch: required={rule.conditions.required_scope}, token={token_scopes}")
            return False
    
    return True
```

**Direct API Protection**:
```python
# src/domain/services/action_service.py
async def execute_action(self, ..., token_claims: dict):
    # Reject tokens with MCP scope trying to access API directly
    if "mcp:use" in token_claims.get("scope", []) and not token_claims.get("acting_as"):
        raise HTTPException(
            status_code=403,
            detail="MCP-scoped tokens cannot be used for direct API access"
        )
```

**Acceptance Criteria**:
- ✅ Policy engine evaluates `required_scope` condition
- ✅ Tokens with `mcp:use` scope rejected for direct API calls
- ✅ Tokens without `acting_as` claim fail MCP tool invocation
- ✅ Audit logs show scope validation failures

---

### FR-003: Authentication Freshness (Step-Up Auth)

**Specification**: Sensitive capabilities require recent authentication.

**Policy Example**:
```yaml
policies:
  - name: "compensation-requires-fresh-auth"
    principal: "employees"
    capabilities: ["workday.payroll.*"]
    environments: ["prod"]
    effect: "ALLOW"
    conditions:
      require_mfa: true
      max_auth_age_seconds: 300        # ← NEW: Auth must be <5 min old
```

**Enforcement Logic**:
```python
def _evaluate_conditions(self, rule, token_claims, ...):
    # NEW: Freshness check
    if rule.conditions and rule.conditions.max_auth_age_seconds:
        auth_time = token_claims.get("auth_time")
        if not auth_time:
            return False  # No auth_time = deny
        
        current_time = int(time.time())
        auth_age = current_time - auth_time
        
        if auth_age > rule.conditions.max_auth_age_seconds:
            logger.warning(f"Auth too old: {auth_age}s > {rule.conditions.max_auth_age_seconds}s")
            return False
    
    return True
```

**MFA Re-Auth Flow**:
```
1. User requests compensation (auth_time = 10min ago)
2. API checks max_auth_age_seconds (300s)
3. Returns 401 MFA_REQUIRED with re-auth URL
4. User re-authenticates with MFA
5. New token issued (fresh auth_time)
6. Retry succeeds
```

**Acceptance Criteria**:
- ✅ Policy engine evaluates `max_auth_age_seconds`
- ✅ Stale tokens rejected for sensitive capabilities
- ✅ Error response includes re-auth guidance
- ✅ Audit logs show freshness check failures

---

### FR-004: Enhanced Audit Trail

**Specification**: Audit logs must capture token provenance and lifecycle.

**Current Audit Entry**:
```jsonl
{
  "timestamp": "2026-01-28T10:30:00Z",
  "actor": "EMP001",
  "event_type": "workday.payroll.get_compensation",
  "payload": {"employee_id": "EMP001"}
}
```

**Enhanced Audit Entry**:
```jsonl
{
  "timestamp": "2026-01-28T10:30:00Z",
  "actor": "EMP001",
  "acting_through": "mcp-server",           // ← NEW
  "token_type": "exchanged",                // ← NEW: original | exchanged
  "token_scope": ["mcp:use"],               // ← NEW
  "token_issued_at": "2026-01-28T10:28:00Z",
  "token_expires_at": "2026-01-28T10:33:00Z",
  "token_ttl_seconds": 300,                 // ← NEW: proves short-lived
  "token_id": "uuid-current",
  "original_token_id": "uuid-parent",       // ← NEW: audit trail link
  "auth_time": "2026-01-28T10:27:00Z",      // ← NEW: when user actually authed
  "mfa_verified": true,
  "auth_age_seconds": 180,                  // ← NEW: freshness metric
  "capability": "workday.payroll.get_compensation",
  "policy_matched": "employee-self-service",
  "result": "success",
  "latency_ms": 145
}
```

**Implementation**:
```python
# src/adapters/filesystem/logger.py
def log_event(self, event_type: str, payload: dict, token_claims: dict, actor: str):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "event_type": event_type,
        "payload": self._redact(payload),
        
        # Token provenance
        "acting_through": token_claims.get("acting_as"),
        "token_type": "exchanged" if "original_token_id" in token_claims else "original",
        "token_scope": token_claims.get("scope", []),
        "token_id": token_claims.get("jti"),
        "original_token_id": token_claims.get("original_token_id"),
        
        # Temporal metadata
        "token_issued_at": datetime.fromtimestamp(token_claims["iat"]).isoformat(),
        "token_expires_at": datetime.fromtimestamp(token_claims["exp"]).isoformat(),
        "token_ttl_seconds": token_claims["exp"] - token_claims["iat"],
        "auth_time": datetime.fromtimestamp(token_claims.get("auth_time", token_claims["iat"])).isoformat(),
        "auth_age_seconds": int(time.time()) - token_claims.get("auth_time", token_claims["iat"]),
        
        # Security context
        "mfa_verified": "mfa" in token_claims.get("amr", [])
    }
    # ... write to JSONL
```

**Acceptance Criteria**:
- ✅ Audit logs include all new fields
- ✅ Token chain visible via `original_token_id`
- ✅ `acting_through` distinguishes MCP vs direct access
- ✅ `auth_age_seconds` enables freshness analysis

---

### FR-005: MCP Server Token Management

**Specification**: MCP server must exchange tokens before tool invocation.

**Token Acquisition**:
```python
# src/mcp/adapters/auth.py
async def get_mcp_token(user_token: str) -> str:
    """Exchange user token for MCP-scoped token."""
    response = await httpx.post(
        f"{settings.OKTA_ISSUER}/v1/token",
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": user_token,
            "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
            "scope": "mcp:use",
            "audience": settings.CAPABILITY_API_AUDIENCE
        }
    )
    response.raise_for_status()
    return response.json()["access_token"]
```

**Token Caching** (Optional Optimization):
```python
# Cache exchanged tokens per user session
# Key: hash(user_token), Value: (mcp_token, expiry)
# TTL: 4 minutes (safety margin before 5-min expiry)
```

**Tool Wrapper**:
```python
# src/mcp/tools/hcm.py
async def get_employee(ctx: Any, employee_id: str) -> str:
    # 1. Extract user token from context
    user_token = get_token_from_context(ctx)
    if not user_token:
        return "ERROR: Missing authorization token"
    
    # 2. Exchange for MCP token
    try:
        mcp_token = await get_mcp_token(user_token)
    except Exception as e:
        return f"ERROR: Token exchange failed: {str(e)}"
    
    # 3. Call backend with MCP token
    response = await backend_client.call_action(
        domain="workday.hcm",
        action="get_employee",
        parameters={"employee_id": employee_id},
        token=mcp_token  # ← Use exchanged token
    )
    
    return str(response.get("data", {}))
```

**Acceptance Criteria**:
- ✅ MCP server exchanges tokens before backend calls
- ✅ Exchanged tokens used for all API requests
- ✅ Token exchange failures return clear errors
- ✅ (Optional) Token caching reduces exchange overhead

---

## Implementation Plan

### Phase 1: MockOkta Token Exchange (4 hours)

**Tasks**:
1. Add `exchange_token()` method to `MockOktaProvider`
2. Implement `/oauth2/v1/token` endpoint for `token-exchange` grant
3. Write unit tests for exchange flow
4. Validate claim preservation (`auth_time`, `amr`)

**Files Changed**:
- `src/adapters/auth/mock_okta.py`
- `src/adapters/auth/test_mock_okta.py`

**Test Cases**:
```python
def test_token_exchange_reduces_ttl():
    user_token = provider.issue_token("EMP001", ttl_seconds=3600)
    mcp_token = provider.exchange_token(user_token, scope="mcp:use")
    
    user_claims = jwt.decode(user_token, options={"verify_signature": False})
    mcp_claims = jwt.decode(mcp_token, options={"verify_signature": False})
    
    assert (mcp_claims["exp"] - mcp_claims["iat"]) == 300  # 5 min
    assert mcp_claims["auth_time"] == user_claims["auth_time"]  # Preserved
    assert "mcp:use" in mcp_claims["scope"]
    assert mcp_claims["acting_as"] == "mcp-server"
```

---

### Phase 2: Policy Engine Extensions (3 hours)

**Tasks**:
1. Add `required_scope` to `PolicyConditions` schema
2. Add `max_auth_age_seconds` to `PolicyConditions` schema
3. Implement scope validation in `_evaluate_conditions()`
4. Implement freshness validation in `_evaluate_conditions()`
5. Write policy engine tests

**Files Changed**:
- `src/domain/entities/policy.py`
- `src/domain/services/policy_engine.py`
- `tests/unit/domain/test_policy_engine.py`

**Test Cases**:
```python
def test_scope_enforcement():
    policy = load_policy_with_scope_requirement()
    
    # Token without required scope
    result = policy_engine.evaluate(
        capability="workday.payroll.get_compensation",
        token_claims={"scope": ["api:read"]},  # Missing mcp:use
        ...
    )
    assert result.allowed == False
    assert "scope" in result.reason
```

---

### Phase 3: MCP Server Integration (3 hours)

**Tasks**:
1. Implement `get_mcp_token()` in `src/mcp/adapters/auth.py`
2. Update all tool functions to exchange tokens
3. Add error handling for exchange failures
4. Write MCP integration tests

**Files Changed**:
- `src/mcp/adapters/auth.py`
- `src/mcp/tools/*.py` (all tool modules)
- `tests/integration/mcp/test_token_exchange.py`

**Test Cases**:
```python
@pytest.mark.asyncio
async def test_mcp_tool_uses_exchanged_token(mock_backend):
    # Setup: User token with 1-hour TTL
    user_token = provider.issue_token("EMP001", ttl_seconds=3600)
    
    # Invoke MCP tool
    ctx = MockContext(authorization=f"Bearer {user_token}")
    result = await get_employee(ctx, "EMP001")
    
    # Verify backend received exchanged token (not user token)
    backend_token = mock_backend.last_request.headers["Authorization"].split()[1]
    claims = jwt.decode(backend_token, options={"verify_signature": False})
    
    assert (claims["exp"] - claims["iat"]) == 300  # 5 min
    assert "mcp:use" in claims["scope"]
```

---

### Phase 4: Audit Enhancements (2 hours)

**Tasks**:
1. Update `JSONLLogger.log_event()` signature to accept token claims
2. Add token provenance fields to audit entries
3. Update all call sites to pass token claims
4. Validate audit log entries in tests

**Files Changed**:
- `src/adapters/filesystem/logger.py`
- `src/domain/services/action_service.py`
- `src/mcp/lib/logging.py`

---

### Phase 5: Documentation & Demo (2 hours)

**Tasks**:
1. Write `docs/TOKEN_EXCHANGE.md` guide
2. Create demo script showing token flow
3. Update Backstage dashboard to visualize token chains
4. Record demo video for stakeholders

**Deliverables**:
- Step-by-step guide for token exchange
- Bash script demonstrating flow
- Audit log analysis queries

---

## Demo Script

### Live Demonstration: Token Scoping in Action

**Setup**:
```bash
# Start services
uvicorn src.main:app --reload &
python src/mcp/server.py &
```

**Script**:
```bash
#!/bin/bash
set -e

echo "=== Token Scoping Demo ==="

# 1. Get user token (1 hour)
echo "[1] Issuing user token (1-hour TTL)..."
USER_TOKEN=$(curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=password&username=EMP001&password=any" | jq -r .access_token)

echo "User token claims:"
jwt decode $USER_TOKEN | jq '{exp, iat, ttl: (.exp - .iat), scope}'

# 2. Exchange for MCP token (5 min)
echo -e "\n[2] Exchanging for MCP-scoped token (5-min TTL)..."
MCP_TOKEN=$(curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=$USER_TOKEN" \
  -d "scope=mcp:use" | jq -r .access_token)

echo "MCP token claims:"
jwt decode $MCP_TOKEN | jq '{exp, iat, ttl: (.exp - .iat), scope, acting_as, original_token_id}'

# 3. Try to use MCP token for direct API access (should fail)
echo -e "\n[3] Attempting direct API access with MCP token (should fail)..."
curl -s -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer $MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq '.error_code, .message'

# 4. Use MCP token via MCP server (should succeed)
echo -e "\n[4] Using MCP token via MCP server (should succeed)..."
# (Invoke via Chainlit/MCP client - simulated here)
echo "✅ MCP tool invocation successful (audit log below)"

# 5. Check audit log
echo -e "\n[5] Audit trail shows token provenance:"
tail -1 logs/audit.jsonl | jq '{
  actor,
  acting_through,
  token_type,
  token_ttl_seconds,
  token_scope,
  auth_age_seconds
}'

echo -e "\n=== Demo Complete ==="
echo "Key Takeaways:"
echo "  • User tokens live 1 hour, MCP tokens live 5 minutes (92% reduction)"
echo "  • MCP tokens cannot be used for direct API access (scope isolation)"
echo "  • Audit trail clearly shows 'acting_through: mcp-server'"
echo "  • Attack window reduced from 60 minutes to 5 minutes"
```

**Expected Output**:
```
=== Token Scoping Demo ===

[1] Issuing user token (1-hour TTL)...
User token claims:
{
  "exp": 1706449200,
  "iat": 1706445600,
  "ttl": 3600,
  "scope": null
}

[2] Exchanging for MCP-scoped token (5-min TTL)...
MCP token claims:
{
  "exp": 1706445960,
  "iat": 1706445660,
  "ttl": 300,
  "scope": ["mcp:use"],
  "acting_as": "mcp-server",
  "original_token_id": "uuid-of-user-token"
}

[3] Attempting direct API access with MCP token (should fail)...
{
  "error_code": "FORBIDDEN",
  "message": "MCP-scoped tokens cannot be used for direct API access"
}

[4] Using MCP token via MCP server (should succeed)...
✅ MCP tool invocation successful

[5] Audit trail shows token provenance:
{
  "actor": "EMP001",
  "acting_through": "mcp-server",
  "token_type": "exchanged",
  "token_ttl_seconds": 300,
  "token_scope": ["mcp:use"],
  "auth_age_seconds": 60
}

=== Demo Complete ===
```

---

## Metrics & Success Criteria

### Security Metrics

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Token TTL (MCP) | 3600s | 300s | **92% reduction** |
| Privilege Scope | All user capabilities | MCP-only | **Isolation achieved** |
| Audit Granularity | Actor only | Actor + Provenance + Token Chain | **Full traceability** |
| Attack Window | 60 minutes | 5 minutes | **92% reduction** |

### Acceptance Tests

**Test Suite**: `tests/integration/test_token_exchange.py`

```python
class TestTokenExchange:
    def test_exchanged_token_has_reduced_ttl(self):
        """Exchanged tokens must have ≤5 minute TTL."""
        pass
    
    def test_exchanged_token_preserves_auth_time(self):
        """auth_time claim must be copied from original token."""
        pass
    
    def test_mcp_token_rejected_for_direct_api(self):
        """Tokens with mcp:use scope cannot access API directly."""
        pass
    
    def test_sensitive_ops_require_fresh_auth(self):
        """Compensation endpoints reject tokens with auth_time >5 min."""
        pass
    
    def test_audit_log_captures_token_chain(self):
        """Audit entries include original_token_id linking."""
        pass
```

---

## Security Analysis

### Threat Model

**Before Token Exchange**:
```
┌─────────────────────────────────────────────────┐
│ Attack: MCP Server Compromise                   │
├─────────────────────────────────────────────────┤
│ Attacker extracts user token from memory        │
│ Token valid: 60 minutes                         │
│ Privilege: All user capabilities               │
│ Detection: None (looks like normal user)        │
│ Mitigation: Token rotation (1-hour window)      │
└─────────────────────────────────────────────────┘
```

**After Token Exchange**:
```
┌─────────────────────────────────────────────────┐
│ Attack: MCP Server Compromise                   │
├─────────────────────────────────────────────────┤
│ Attacker extracts MCP token from memory         │
│ Token valid: 5 minutes                          │
│ Privilege: MCP operations only (no direct API)  │
│ Detection: Audit shows acting_through=mcp       │
│ Mitigation: Token scope + short TTL             │
└─────────────────────────────────────────────────┘
```

### Residual Risks

1. **MCP Token Still Usable Within 5 Minutes**
   - Mitigation: Monitor for anomalous MCP call patterns
   - Future: Add request fingerprinting (IP, user-agent)

2. **Token Exchange Endpoint Could Be Targeted**
   - Mitigation: Rate limiting on exchange endpoint
   - Future: Require original token's `jti` in exchange request

3. **Chainlit UI Still Holds Full User Token**
   - Acceptable: UI is user-controlled (not shared server)
   - Future: Consider browser-based exchange (avoid server-side storage)

---

## Rollout Plan

### Phase 1: Mock Environment (Week 1)
- Implement token exchange in MockOkta
- Deploy to local/dev environments
- Run integration tests

### Phase 2: Policy Updates (Week 1)
- Add scope requirements to policies
- Test with existing fixtures
- Document policy changes

### Phase 3: MCP Integration (Week 2)
- Update MCP server to exchange tokens
- Deploy to staging
- Validate with Chainlit client

### Phase 4: Audit Enhancements (Week 2)
- Roll out enhanced logging
- Build Backstage dashboard
- Train team on audit queries

### Phase 5: Production (Week 3)
- Deploy to production
- Monitor metrics
- Prepare rollback plan (feature flag)

---

## Open Questions

1. **Token Caching**: Should MCP cache exchanged tokens (4-min TTL) or exchange on every request?
   - **Recommendation**: Cache with 4-min TTL to reduce load on exchange endpoint
   
2. **User Experience**: How to handle token exchange failures gracefully?
   - **Recommendation**: Return user-friendly error with re-auth link
   
3. **Scope Granularity**: Should we have separate scopes for read vs write operations?
   - **Recommendation**: Start with `mcp:use`, add `mcp:write` in Phase 2 if needed

4. **Backwards Compatibility**: Should we support direct API access during transition?
   - **Recommendation**: No - enforce immediately to avoid confusion

---

## References

- **RFC 8693**: OAuth 2.0 Token Exchange
- **NIST SP 800-63B**: Digital Identity Guidelines (Authentication)
- **OWASP Token Best Practices**: https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html

---

## Appendix: Configuration Examples

### Policy with Scope Requirement
```yaml
# config/policy-workday.yaml
policies:
  - name: "mcp-users-scoped-access"
    principal:
      type: HUMAN
      okta_group: "employees"
    capabilities: ["workday.*"]
    environments: ["local", "dev", "prod"]
    effect: "ALLOW"
    conditions:
      required_scope: "mcp:use"
      max_ttl_seconds: 300
```

### Policy with Freshness Requirement
```yaml
policies:
  - name: "compensation-fresh-auth-required"
    principal:
      type: HUMAN
      okta_group: "employees"
    capabilities: ["workday.payroll.get_compensation"]
    environments: ["prod"]
    effect: "ALLOW"
    conditions:
      require_mfa: true
      max_auth_age_seconds: 300  # 5 minutes
```

---

**End of PRD**