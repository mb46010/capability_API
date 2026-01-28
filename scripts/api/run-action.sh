#!/bin/bash
# run-action.sh: Helper to execute an action for a specific persona

set -e

BASE_URL=${BASE_URL:-"http://localhost:8000"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PERSONA=$1
DOMAIN=$2
ACTION=$3
PARAMS=${4:-"{}"}

if [ -z "$PERSONA" ] || [ -z "$DOMAIN" ] || [ -z "$ACTION" ]; then
  echo "Usage: $0 <persona> <domain> <action> '<params_json>'";
  echo "Example: $0 user workday.hcm get_employee '{\"employee_id\": \"EMP001\"}'";
  exit 1
fi

# 1. Get Token
TOKEN=$("$SCRIPT_DIR/get-token.sh" "$PERSONA")

# 2. Run Action
echo "Executing $DOMAIN.$ACTION as $PERSONA..." >&2
curl -s -X POST "$BASE_URL/actions/$DOMAIN/$ACTION" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"parameters\": $PARAMS
  }" | jq '.'
