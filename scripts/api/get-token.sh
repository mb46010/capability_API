#!/bin/bash
# get-token.sh: Helper to obtain OIDC tokens for testing personas

set -e

BASE_URL=${BASE_URL:-"http://localhost:8000"}
PERSONA=${1:-"admin"}

case $PERSONA in
  "admin")
    SUB="admin@local.test"
    CLAIMS='{}'
    ;;
  "user"|"EMP001")
    SUB="EMP001"
    CLAIMS='{}'
    ;;
  "agent")
    SUB="agent-assistant@local.test"
    CLAIMS='{}'
    ;;
  "mfa")
    SUB="admin@local.test"
    CLAIMS='{"amr": ["mfa", "pwd"]}'
    ;;
  *)
    SUB=$PERSONA
    CLAIMS='{}'
    ;;
esac

# Use the test token endpoint for ease of claim injection
TOKEN=$(curl -s -X POST "$BASE_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -d "{
    \"subject\": \"$SUB\",
    \"additional_claims\": $CLAIMS
  }" | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "Error: Failed to obtain token. Is the server running at $BASE_URL?" >&2
  exit 1
fi

echo "$TOKEN"
