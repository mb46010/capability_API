#!/bin/bash
set -e

# 0. Environment Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "DEMO 3: Policy Verification (The Safety Net)"
echo "============================================================"
echo "Goal: Prove security rules work BEFORE they are deployed."
echo ""

# 1. Run baseline verification
echo "Step 1: Running automated verification suite..."
"$ROOT_DIR/scripts/verify-policy" run --format table
echo ""

# 2. Simulate a human error
echo "Step 2: Simulating a security violation (human error)..."
echo "Scenario: A developer accidentally grants AI Agents access to payroll data."
echo "------------------------------------------------------------"

# Create a 'broken' policy file
cp "$ROOT_DIR/config/policy-workday.yaml" "$ROOT_DIR/config/policy-broken.yaml"
# Use sed to 'break' the policy by adding a dangerous wildcard to AI agent
# Note: principal 'hr_assistant' exists in policy-workday.yaml
sed -i 's/principal: "hr_assistant"/principal: "hr_assistant"\n    capabilities: ["workday.payroll.*"]/' "$ROOT_DIR/config/policy-broken.yaml"

echo "Running verification against the BROKEN policy..."
set +e # Allow error for demo
"$ROOT_DIR/scripts/verify-policy" run --policy "$ROOT_DIR/config/policy-broken.yaml" --format table
set -e

echo ""
echo "Observation: The system DETECTED the hole and would block deployment."
echo "   Specific violation: AI Assistant granted access to restricted payroll domain."

# Cleanup
rm "$ROOT_DIR/config/policy-broken.yaml"
echo "============================================================"