#!/bin/bash
set -e

# Clear screen for fresh start
clear

echo "############################################################"
echo "#                                                          #"
# HR AI Platform Stakeholder Demo
echo "#                                                          #"
echo "############################################################"
echo ""
echo "This demo will walk through the core security and trust"
echo "capabilities of the HR Capability API."
echo ""
echo "Components being demonstrated:"
echo "1. AI Guardrails (Field filtering & MFA)"
echo "2. AI Token Exchange (Scoped task passes)"
echo "3. Policy Verification (The automated safety net)"
echo "4. Compliance Reporting (Audit evidence)"
echo ""
read -p "Press [Enter] to start Demo 1..."

./scripts/demo/demo-1-guardrails.sh

echo ""
read -p "Press [Enter] to start Demo 2..."

./scripts/demo/demo-2-token-exchange.sh

echo ""
read -p "Press [Enter] to start Demo 3..."

./scripts/demo/demo-3-policy-verification.sh

echo ""
read -p "Press [Enter] to start Demo 4..."

./scripts/demo/demo-4-compliance-report.sh

echo ""
echo "############################################################"
echo "# STAKEHOLDER DEMO COMPLETE                                #"
echo "############################################################"
echo "Next Steps: Review the HTML report in tests/policy/reports/demo_report.html"
echo ""
