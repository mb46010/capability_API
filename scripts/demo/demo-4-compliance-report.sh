#!/bin/bash
set -e

echo "============================================================"
echo "DEMO 4: Compliance & Audit Reporting"
echo "============================================================"
echo "Goal: Generate an audit-ready evidence report for stakeholders."
echo ""

REPORT_FILE="tests/policy/reports/demo_report.html"
mkdir -p tests/policy/reports

echo "Generating HTML report..."
./scripts/verify-policy run --format html > $REPORT_FILE

echo ""
echo "✅ Report generated successfully!"
echo "   Location: $REPORT_FILE"
echo ""
echo "Stakeholders can review this report to see 100% proof of policy enforcement."
echo "Each test case is mapped to a documented security requirement (e.g., SEC-001)."
echo "============================================================"
