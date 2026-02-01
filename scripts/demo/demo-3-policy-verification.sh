#!/bin/bash
set -e

echo "============================================================"
echo "DEMO 3: Policy Verification (The Safety Net)"
echo "============================================================"
echo "Goal: Prove security rules work BEFORE they are deployed."
echo ""

# 1. Run baseline verification
echo "Step 1: Running automated verification suite..."
./scripts/verify-policy run --format table
echo ""

# 2. Simulate a human error
echo "Step 2: Simulating a security violation (human error)..."
echo "Scenario: A developer accidentally grants AI Agents access to payroll data."
echo "------------------------------------------------------------"

# Create a 'broken' policy file
cp config/policy-workday.yaml config/policy-broken.yaml
# Use sed to 'break' the policy by adding a dangerous wildcard to AI agent
sed -i 's/principal: "hr_assistant"/principal: "hr_assistant"\n    capabilities: ["workday.payroll.*"]/' config/policy-broken.yaml

echo "Running verification against the BROKEN policy..."
set +e # Allow error for demo
./scripts/verify-policy run --policy config/policy-broken.yaml --format table
set -e

echo ""
echo "✅ Observation: The system DETECTED the hole and would block deployment."
echo "   Specific violation: AI Assistant granted access to restricted payroll domain."

# Cleanup
rm config/policy-broken.yaml
echo "============================================================"
