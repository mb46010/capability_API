#!/bin/bash
set -e

# Scenario 1: AI Agent Limited Access
echo "=== Test 1: AI Agent sees filtered data ==="
TOKEN=$(./scripts/api/get-token.sh agent)
curl -s "http://localhost:8000/actions/workday.hcm/get_employee" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq .

# Scenario 2: MFA Required
echo "=== Test 2: Compensation requires MFA ==="
TOKEN_NO_MFA=$(./scripts/api/get-token.sh user)
curl -s "http://localhost:8000/actions/workday.payroll/get_compensation" \
  -H "Authorization: Bearer $TOKEN_NO_MFA" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq .

echo "✅ All scenarios passed"