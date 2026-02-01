#!/bin/bash
set -e

# Configuration
API_URL="http://localhost:8000"
AUTH_URL="http://localhost:8000/auth"

echo "============================================================"
echo "DEMO 1: AI Guardrails & MFA Enforcement"
echo "============================================================"
echo "Goal: Show how the Capability API protects sensitive data."
echo ""

# Ensure server is running (check port 8000)
if ! curl -s "$API_URL/health" > /dev/null; then
    echo "Error: Capability API is not running. Please run 'python src/main.py' first."
    exit 1
fi

# 1. AI Agent Limited Access
echo "Step 1: AI Agent querying employee data..."
echo "Scenario: AI assistant looks up employee 'EMP001'"
echo "------------------------------------------------------------"

AGENT_TOKEN=$(curl -s -X POST "$AUTH_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -d '{"subject": "agent-assistant@local.test", "principal_type": "AI_AGENT"}' | jq -r .access_token)

echo "Response for AI Agent:"
curl -s -X POST "$API_URL/actions/workday.hcm/get_employee" \
  -H "Authorization: Bearer $AGENT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq '{allowed, result}'

echo ""
echo "Observation: Sensitive fields (salary, SSN) are filtered out for AI Agents."
echo ""

# 2. MFA Enforcement
echo "Step 2: Accessing compensation data..."
echo "Scenario: Human employee tries to view their own salary."
echo "------------------------------------------------------------"

USER_TOKEN=$(curl -s -X POST "$AUTH_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -d '{"subject": "EMP001", "principal_type": "HUMAN", "groups": ["employees"]}' | jq -r .access_token)

echo "Attempt WITHOUT MFA:"
curl -s -X POST "$API_URL/actions/workday.payroll/get_compensation" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq '{allowed, error}'

echo ""
echo "Attempt WITH MFA:"
MFA_TOKEN=$(curl -s -X POST "$AUTH_URL/test/tokens" \
  -H "Content-Type: application/json" \
  -d '{"subject": "EMP001", "principal_type": "HUMAN", "groups": ["employees"], "additional_claims": {"amr": ["mfa", "pwd"]}}' | jq -r .access_token)

curl -s -X POST "$API_URL/actions/workday.payroll/get_compensation" \
  -H "Authorization: Bearer $MFA_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"parameters": {"employee_id": "EMP001"}}' | jq '{allowed, result: (.result | {salary: "****", currency})}'

echo ""
echo "Observation: Sensitive payroll actions require Multi-Factor Authentication (MFA)."
echo "============================================================"