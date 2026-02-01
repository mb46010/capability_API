#!/bin/bash
# get-token.sh: Helper to obtain OIDC tokens for testing personas

set -e

BASE_URL=${BASE_URL:-"http://localhost:8000/auth"}
PERSONA=${1:-"admin"}

case $PERSONA in
  "admin")
    SUB="admin@local.test"
    TEST_GROUPS='["hr-platform-admins"]'
    CLAIMS='{}'
    ;;
  "user"|"EMP001")
    SUB="EMP001"
    TEST_GROUPS='["employees"]'
    CLAIMS='{}'
    ;;
  "agent")
    SUB="agent-assistant@local.test"
    TEST_GROUPS='[]'
    CLAIMS='{}'
    ;;
  "mfa")
    SUB="admin@local.test"
    TEST_GROUPS='["hr-platform-admins"]'
    CLAIMS='{"amr": ["mfa", "pwd"]}'
    ;;
  *)
    SUB=$PERSONA
    TEST_GROUPS='[]'
    CLAIMS='{}'
    ;;
esac

# Use the test token endpoint for ease of claim injection
TOKEN=$(curl -s -X POST "$BASE_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -H "X-Test-Secret: ${MOCK_OKTA_TEST_SECRET:-mock-okta-secret}" \
  -d "{
    \"subject\": \"$SUB\",
    \"groups\": $TEST_GROUPS,
    \"additional_claims\": $CLAIMS
  }" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "Error: Failed to obtain token. Is the server running at $BASE_URL?" >&2
  exit 1
fi

echo "$TOKEN"
