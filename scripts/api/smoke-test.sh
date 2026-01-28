#!/bin/bash
# smoke-test.sh: End-to-end verification of common scenarios

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "--- 1. AI Agent: Public Directory Lookup ---"
"$SCRIPT_DIR/run-action.sh" agent workday.hcm get_employee '{"employee_id": "EMP001"}'

echo -e "\n--- 2. User: Check Own Balance ---"
"$SCRIPT_DIR/run-action.sh" user workday.time/get_balance '{"employee_id": "EMP001"}'

echo -e "\n--- 3. User: Request Time Off ---"
"$SCRIPT_DIR/run-action.sh" user workday.time/request '{
  "employee_id": "EMP001",
  "type": "PTO",
  "start_date": "2026-05-01",
  "end_date": "2026-05-05",
  "hours": 40
}'

echo -e "\n--- 4. Security Check: Compensation WITHOUT MFA (Expect Failure) ---"
"$SCRIPT_DIR/run-action.sh" admin workday.payroll/get_compensation '{"employee_id": "EMP001"}'

echo -e "\n--- 5. Security Check: Compensation WITH MFA (Expect Success) ---"
"$SCRIPT_DIR/run-action.sh" mfa workday.payroll/get_compensation '{"employee_id": "EMP001"}'

echo -e "\n--- 6. Manager: List Direct Reports ---"
"$SCRIPT_DIR/run-action.sh" admin workday.hcm/list_direct_reports '{"manager_id": "EMP042"}'

echo -e "\nSmoke test sequence initiated."
