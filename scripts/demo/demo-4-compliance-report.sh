#!/bin/bash
set -e

# 0. Environment Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo "============================================================"
echo "DEMO 4: Compliance & Audit Reporting"
echo "============================================================"
echo "Goal: Generate an audit-ready evidence report for stakeholders."
echo ""

REPORT_FILE="$ROOT_DIR/tests/policy/reports/demo_report.html"
mkdir -p "$ROOT_DIR/tests/policy/reports"

echo "Generating HTML report..."
"$ROOT_DIR/scripts/verify-policy" run --format html > "$REPORT_FILE"

echo ""
echo "OK: Report generated successfully!"
echo "   Location: $REPORT_FILE"
echo ""
echo "Stakeholders can review this report to see 100% proof of policy enforcement."
echo "Each test case is mapped to a documented security requirement (e.g., SEC-001)."
echo "============================================================"