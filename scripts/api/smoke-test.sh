#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:8000"
AUTH_URL="http://localhost:8000/auth"

echo "=== Capability API Smoke Test ==="

# 1. Health Check
echo "[1] Checking system health..."
curl -s -f "$API_URL/health" > /dev/null
echo "✅ System healthy"

# 2. Authentication
echo "[2] Obtaining test token..."
TOKEN=$(curl -s -X POST "$AUTH_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -d '{"subject": "admin@local.test", "principal_type": "HUMAN", "groups": ["hr-platform-admins"], "additional_claims": {"amr": ["mfa"]}}' | jq -r .access_token)

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "❌ Failed to obtain token"
    exit 1
fi
echo "✅ Token obtained"

# 3. Action Execution (HCM)
echo "[3] Testing HCM action (get_employee)..."
curl -s -f -X POST "$API_URL/actions/workday.hcm/get_employee" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq -e '.data.employee_id == "EMP001"' > /dev/null
echo "✅ HCM action successful"

# 4. Action Execution (Payroll + MFA)
echo "[4] Testing Payroll action (get_compensation)..."
curl -s -f -X POST "$API_URL/actions/workday.payroll/get_compensation" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq -e '.meta.security.mfa_verified == true' > /dev/null
echo "✅ Payroll action successful (MFA verified)"

# 5. Policy Verification CLI
echo "[5] Running policy verification suite..."
./scripts/verify-policy run --format json | jq -e '.summary.failed == 0' > /dev/null
echo "✅ Policy verification passed"

echo ""
echo "#######################################"
echo "# ALL SMOKE TESTS PASSED              #"
echo "#######################################"
