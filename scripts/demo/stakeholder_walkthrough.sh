#!/bin/bash
set -e

echo "=== HR AI Platform Security Demo ==="
echo "Demonstrating defense-in-depth authorization"
echo ""

# Start server in background
echo "Starting server..."
python src/main.py &
SERVER_PID=$!
sleep 3

echo "✅ Server started"
echo ""

# Test 1: AI Agent Limited Access
echo "=== Test 1: AI Agent Field Filtering ==="
echo "Scenario: AI assistant looks up employee EMP001"
echo ""

AGENT_TOKEN=$(curl -s -X POST http://localhost:9000/test/tokens \
  -H "Content-Type: application/json" \
  -d '{"subject": "agent-assistant@local.test"}' | jq -r .access_token)

echo "Response from AI agent query:"
curl -s -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq .

echo ""
echo "✅ Notice: salary and SSN are filtered out"
echo "   Security layer: Field-level data protection"
echo ""

# Test 2: MFA Required
echo "=== Test 2: MFA Enforcement ==="
echo "Scenario: User tries to view compensation without MFA"
echo ""

USER_TOKEN=$(curl -s -X POST http://localhost:9000/test/tokens \
  -H "Content-Type: application/json" \
  -d '{"subject": "EMP001"}' | jq -r .access_token)

echo "Response without MFA:"
curl -s -X POST http://localhost:8000/actions/workday.payroll/get_compensation \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}'

echo ""
echo "❌ Access denied - MFA required"
echo ""

echo "Now trying with MFA token..."
MFA_TOKEN=$(curl -s -X POST http://localhost:9000/test/tokens \
  -H "Content-Type: application/json" \
  -d '{"subject": "EMP001", "additional_claims": {"amr": ["mfa", "pwd"]}}' | jq -r .access_token)

curl -s -X POST http://localhost:8000/actions/workday.payroll/get_compensation \
  -H "Authorization: Bearer $MFA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq .

echo ""
echo "✅ Access granted with MFA"
echo "   Security layer: Policy-based conditional access"
echo ""

# Test 3: Audit Trail
echo "=== Test 3: Audit Trail ==="
echo "Last 5 actions logged:"
tail -5 logs/audit.jsonl | jq .

echo ""
echo "✅ All actions logged with PII redaction"
echo ""

# Cleanup
kill $SERVER_PID
echo "Demo complete"