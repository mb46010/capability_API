#!/bin/bash
set -e

echo "=== Token Scoping Demo ==="

# 1. Get user token (1 hour)
echo "[1] Issuing user token (1-hour TTL)..."
USER_TOKEN=$(curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=password&username=user@local.test&password=any" | jq -r .access_token)

if [ "$USER_TOKEN" == "null" ]; then
    echo "Error: Failed to get user token"
    exit 1
fi

echo "User token claims:"
# Decode without verifying signature for demo purposes
# Note: In real scenarios use proper verification
echo "$USER_TOKEN" | awk -F. '{print $2}' | base64 -d 2>/dev/null | jq '{exp, iat, ttl: (.exp - .iat), scope}'

# 2. Exchange for MCP token (5 min)
echo -e "\n[2] Exchanging for MCP-scoped token (5-min TTL)..."
MCP_TOKEN=$(curl -s -X POST http://localhost:9000/oauth2/v1/token \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=$USER_TOKEN" \
  -d "scope=mcp:use" | jq -r .access_token)

if [ "$MCP_TOKEN" == "null" ]; then
    echo "Error: Failed to exchange token"
    exit 1
fi

echo "MCP token claims:"
echo "$MCP_TOKEN" | awk -F. '{print $2}' | base64 -d 2>/dev/null | jq '{exp, iat, ttl: (.exp - .iat), scope, acting_as, original_token_id}'

# 3. Try to use MCP token for direct API access (should fail)
echo -e "\n[3] Attempting direct API access with MCP token (should fail)..."
# We'll use a known valid endpoint like list_pay_statements which requires MFA and is sensitive
# Or get_employee which is standard.
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer $MCP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}')

if [ "$RESPONSE" == "403" ]; then
    echo "✅ Success: Direct API access rejected with 403 Forbidden"
else
    echo "❌ Failure: Direct API access returned $RESPONSE (Expected 403)"
fi

echo -e "\n=== Demo Complete ==="
