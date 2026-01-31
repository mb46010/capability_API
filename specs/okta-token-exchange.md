# Token Scoping Options (High Level)
Current Design
Problem: MCP gets full user token, can do anything user can do for entire token lifetime (1 hour for humans).

## Token Exchange (OAuth Token Exchange - RFC 8693)
What: Swap user's long-lived token for short-lived, scoped token
How:

User token → Okta exchange → MCP-scoped token (5 min, can only call MCP)
MCP uses scoped token → API validates it

AWS/Okta: Native support via token exchange endpoint
Complexity: Medium (need exchange endpoint config)
Security win: Big - limits blast radius if MCP compromised

## Step-Up Authentication for Sensitive Operations
What: MFA-required capabilities need fresh token (<5 min old)
How:

Policy condition: max_token_age: 300 for workday.payroll.*
Forces re-auth for sensitive ops even if session is active

AWS/Okta: Check auth_time claim in JWT
Complexity: Low (already have MFA checks)
Security win: Medium - time-based freshness

Implementation:
User logs in → 1hr token
Chainlit → Token exchange → 5min MCP token
MCP uses scoped token → API validates
Sensitive op → Requires fresh (<5min) MFA token


## Enhanced Audit with Token Context
From current:
{"timestamp": "...", "actor": "EMP001", "event_type": "workday.hcm.get_employee", "payload": {...}}

To:

{
  "timestamp": "2026-01-28T10:30:00Z",
  "actor": "EMP001",
  "acting_through": "mcp-server",           // NEW
  "token_type": "exchanged",                // NEW: original vs exchanged
  "token_issued_at": "2026-01-28T10:28:00Z",
  "token_expires_at": "2026-01-28T10:33:00Z",
  "token_ttl_seconds": 300,                 // NEW: proves short-lived
  "mfa_verified": true,
  "auth_time": "2026-01-28T10:27:00Z",      // NEW: when user actually authed
  "capability": "workday.payroll.get_compensation",
  "policy_matched": "employee-self-service",
  "result": "success",
  "latency_ms": 145
}

## Mock Token Exchange Flow
1. User Token (1 hour)
json{
  "sub": "EMP001",
  "principal_type": "HUMAN",
  "groups": ["employees"],
  "amr": ["mfa", "pwd"],
  "auth_time": 1706445600,
  "iat": 1706445600,
  "exp": 1706449200  // +1 hour
}
2. Chainlit Calls Mock Exchange
pythonresponse = httpx.post(
    "http://localhost:9000/oauth2/v1/token",
    data={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": user_token,
        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "requested_token_type": "urn:ietf:params:oauth:token-type:access_token",
        "scope": "mcp:use"
    }
)
3. Mock Returns Scoped Token (5 min)
json{
  "sub": "EMP001",
  "principal_type": "HUMAN",
  "groups": ["employees"],
  "amr": ["mfa", "pwd"],
  "auth_time": 1706445600,      // Preserved from original
  "iat": 1706445660,            // NEW: issued 1 min later
  "exp": 1706445960,            // NEW: +5 min only
  "scope": ["mcp:use"],         // NEW: restricted scope
  "acting_as": "mcp-server",    // NEW: provenance
  "original_token_id": "uuid-of-user-token"  // NEW: audit trail
}

Demo Value: What You Can Show
Live Demo Script
Scenario: Token Scoping in Action
bash# 1. Get user token (1 hour)
USER_TOKEN=$(curl -s POST .../token -d "grant_type=password&username=EMP001" | jq -r .access_token)
jwt decode $USER_TOKEN | jq .exp  # Shows 3600 seconds

# 2. Exchange for MCP token (5 min)
MCP_TOKEN=$(curl -s POST .../token -d "grant_type=token-exchange&subject_token=$USER_TOKEN&scope=mcp:use" | jq -r .access_token)
jwt decode $MCP_TOKEN | jq .exp  # Shows 300 seconds
jwt decode $MCP_TOKEN | jq .scope  # Shows ["mcp:use"]

# 3. Try to use MCP token outside MCP context
curl -H "Authorization: Bearer $MCP_TOKEN" http://localhost:8000/actions/workday.hcm/get_employee
# Response: 403 "Token scope 'mcp:use' not valid for direct API access"

# 4. Use via MCP (works)
# MCP server validates scope, then calls API

# 5. Check audit log
tail -1 logs/audit.jsonl | jq
# Shows: acting_through="mcp-server", token_ttl_seconds=300
Stakeholder takeaway:
"Even if the MCP server is compromised, the attacker only has a 5-minute window and can't use the token outside MCP context."

Recommended Mock Additions
Add to MockOktaProvider
pythondef exchange_token(
    self,
    subject_token: str,
    scope: str = "mcp:use",
    ttl_seconds: int = 300
) -> str:
    """
    Implement RFC 8693 token exchange.
    Returns new token with reduced TTL and custom scope.
    """
    # Verify original token
    original_claims = self.verify_token(subject_token)
    
    # Create new token with restricted scope
    new_claims = {
        **original_claims,
        "scope": [scope],
        "acting_as": "mcp-server",
        "original_token_id": original_claims["jti"],
        "auth_time": original_claims.get("auth_time", original_claims["iat"])
    }
    
    return self.issue_token(
        subject=original_claims["sub"],
        ttl_seconds=ttl_seconds,
        additional_claims=new_claims
    )
Add to PolicyEngine
pythondef _evaluate_conditions(self, rule, ...):
    # Existing checks...
    
    # NEW: Scope check
    if rule.conditions.required_scope:
        token_scope = token_claims.get("scope", [])
        if rule.conditions.required_scope not in token_scope:
            return False
    
    # NEW: Freshness check
    if rule.conditions.max_auth_age_seconds:
        auth_time = token_claims.get("auth_time", token_issued_at)
        age = current_time - auth_time
        if age > rule.conditions.max_auth_age_seconds:
            return False