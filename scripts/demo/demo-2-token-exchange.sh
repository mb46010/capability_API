#!/bin/bash
set -e

# Configuration
AUTH_URL="http://localhost:8000/auth"
API_URL="http://localhost:8000"

echo "============================================================"
echo "DEMO 2: AI Token Exchange & Scoping"
echo "============================================================"
echo "Goal: Show how we reduce 'blast radius' using short-lived tokens."
echo ""

# 1. Get user token (Long-lived)
echo "Step 1: User authenticates (1-hour session)..."
USER_TOKEN=$(curl -s -X POST "$AUTH_URL/oauth2/v1/token" \
  -d "grant_type=password&username=user@local.test&password=any" | jq -r .access_token)

echo "User Token (Last 10 chars): ...${USER_TOKEN: -10}"
echo ""

# 2. Exchange for AI token (Short-lived)
echo "Step 2: AI Agent exchanges user token for a 'Task Pass' (5-min session)..."
MCP_TOKEN=$(curl -s -X POST "$AUTH_URL/oauth2/v1/token" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=$USER_TOKEN" \
  -d "scope=mcp:use" | jq -r .access_token)

echo "AI Task Token Claims:"
echo "$MCP_TOKEN" | awk -F. '{print $2}' | base64 -d 2>/dev/null | jq '{scope, ttl: (.exp - .iat), acting_as}'
echo ""

# 3. Security Check
echo "Step 3: Verifying scope enforcement..."
echo "Scenario: AI tries to use its scoped token to call the API directly."
echo "------------------------------------------------------------"

RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$API_URL/actions/workday.hcm/get_employee" \
  -H "Authorization: Bearer $MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}')

if [ "$RESPONSE" == "403" ]; then
    echo "✅ Success: Direct API access REJECTED (403 Forbidden)."
    echo "   The token is only valid when used through the proper AI Gateway."
else
    echo "❌ Failure: Expected 403, got $RESPONSE"
fi

echo "============================================================"
