#!/bin/bash

# Capability API Smoke Test
# This script validates the core happy path of the API.
# It is designed to be robust and safe for both direct execution and sourcing.

run_smoke_test() {
    # 0. Environment Setup
    # Get the directory where this script is located
    local SCRIPT_DIR
    SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
    
    # Change to the project root (two levels up from scripts/api/)
    local ROOT_DIR
    ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
    
    if [ ! -d "$ROOT_DIR" ]; then
        echo "Error: Could not determine project root directory."
        return 1
    fi
    
    cd "$ROOT_DIR"

    local API_URL="http://localhost:8000"
    local AUTH_URL="http://localhost:8000/auth"

    echo "=== Capability API Smoke Test ==="

    # Check for prerequisites
    if ! command -v jq >/dev/null 2>&1; then
        echo "Error: 'jq' is not installed. Please install it to run smoke tests."
        return 1
    fi

    if ! command -v curl >/dev/null 2>&1; then
        echo "Error: 'curl' is not installed."
        return 1
    fi

    # 1. Health Check
    echo "[1] Checking system health..."
    if ! curl -s -f "$API_URL/health" > /dev/null; then
        echo "Error: Capability API is not reachable at $API_URL"
        echo "Make sure to run 'python src/main.py' first."
        return 1
    fi
    echo "OK: System healthy"

    # 2. Authentication
    echo "[2] Obtaining test token..."
    local TOKEN_JSON
    TOKEN_JSON=$(curl -s -X POST "$AUTH_URL/test/tokens" \
      -H "Content-Type: application/json" \
      -H "X-Test-Secret: ${MOCK_OKTA_TEST_SECRET}" \
      -d '{"subject": "EMP001", "principal_type": "HUMAN", "groups": ["employees"], "additional_claims": {"amr": ["mfa"]}}' 2>/dev/null)

    if [ -z "$TOKEN_JSON" ]; then
        echo "Error: Failed to obtain response from $AUTH_URL"
        return 1
    fi

    local TOKEN
    TOKEN=$(echo "$TOKEN_JSON" | jq -r .access_token 2>/dev/null)

    if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
        echo "Error: Failed to extract token from response"
        echo "$TOKEN_JSON"
        return 1
    fi
    echo "OK: Token obtained"

    # 3. Action Execution (HCM)
    echo "[3] Testing HCM action (get_employee)..."
    local HCM_RESP
    HCM_RESP=$(curl -s -f -X POST "$API_URL/actions/workday.hcm/get_employee" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"parameters": {"employee_id": "EMP001"}}' 2>/dev/null)

    if [ -z "$HCM_RESP" ] || ! echo "$HCM_RESP" | jq -e '.data.employee_id == "EMP001"' > /dev/null 2>&1; then
        echo "Error: HCM action failed or returned unexpected data"
        echo "$HCM_RESP"
        return 1
    fi
    echo "OK: HCM action successful"

    # 4. Action Execution (Payroll + MFA)
    echo "[4] Testing Payroll action (get_compensation)..."
    local PAY_RESP
    PAY_RESP=$(curl -s -f -X POST "$API_URL/actions/workday.payroll/get_compensation" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"parameters": {"employee_id": "EMP001"}}' 2>/dev/null)

    if [ -z "$PAY_RESP" ] || ! echo "$PAY_RESP" | jq -e '.meta.security.mfa_verified == true' > /dev/null 2>&1; then
        echo "Error: Payroll action failed MFA verification check"
        echo "$PAY_RESP"
        return 1
    fi
    echo "OK: Payroll action successful (MFA verified)"

    # 5. Policy Verification CLI
    echo "[5] Running policy verification suite..."
    if ! ./scripts/verify-policy run --format json 2>/dev/null | jq -e '.summary.failed == 0' > /dev/null 2>&1; then
        echo "Error: Policy verification suite failed"
        return 1
    fi
    echo "OK: Policy verification passed"

    # 6. Backstage Catalog Sync
    echo "[6] Checking Backstage catalog synchronization..."
    export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"
    if ! python3 scripts/generate_catalog.py --check > /dev/null 2>&1; then
        echo "Error: Backstage catalog is out of sync or generator failed"
        echo "Try running: python3 scripts/generate_catalog.py"
        return 1
    fi
    echo "OK: Catalog synchronized"

    # 7. Governance Report
    echo "[7] Verifying governance dashboard report..."
    if [ ! -f "docs/policy-verification/latest.md" ]; then
        echo "Error: Policy verification Markdown report was not generated"
        return 1
    fi
    echo "OK: Governance report exists"

    echo ""
    echo "#######################################"
    echo "# ALL SMOKE TESTS PASSED              #"
    echo "#######################################"
    return 0
}

# Execute in a subshell or return if sourced to prevent terminal from closing
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    run_smoke_test
    exit $?
else
    run_smoke_test
fi
