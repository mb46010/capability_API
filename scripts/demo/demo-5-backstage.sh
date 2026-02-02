#!/bin/bash
set -e

# 0. Environment Setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
export PYTHONPATH="$ROOT_DIR:$PYTHONPATH"

echo "============================================================"
echo "DEMO 5: Backstage.io Governance Lens"
echo "============================================================"
echo "Goal: Show how we make governance visible and browsable."
echo ""

# 1. Generate Catalog
echo "Step 1: Synchronizing Capability Registry with Backstage..."
echo "------------------------------------------------------------"
python3 "$ROOT_DIR/scripts/generate_catalog.py"
echo "OK: Catalog entities generated in 'catalog/'"
echo ""

# 2. Show a specific entity
echo "Step 2: Inspecting a generated entity (workday.hcm.get_employee)..."
echo "------------------------------------------------------------"
cat "$ROOT_DIR/catalog/workday-hcm/get_employee.yaml" | grep -E "name:|capability-api/governed-by:"
echo ""
echo "Observation: The entity automatically includes a 'Governed By' section"
echo "listing every policy that grants access to this specific action."
echo ""

# 3. Show composite capability flow
echo "Step 3: Visualizing a composite capability orchestration..."
echo "------------------------------------------------------------"
echo "Capability: hr.onboarding.prepare_workspace"
cat "$ROOT_DIR/catalog/hr-onboarding/prepare_workspace.yaml" | grep -A 10 "mermaid"
echo ""
echo "Observation: Composite capabilities include Mermaid diagrams that"
echo "Backstage renders as visual flowcharts for non-technical stakeholders."
echo ""

# 4. Show Verification Report
echo "Step 4: Inspecting the TechDocs Verification Dashboard..."
echo "------------------------------------------------------------"
# Ensure report exists
"$ROOT_DIR/scripts/verify-policy" run --format table > /dev/null
head -n 15 "$ROOT_DIR/docs/policy-verification/latest.md"
echo "..."
echo ""
echo "Observation: The system generates a native Markdown report for TechDocs"
echo "providing a web-accessible view of our 100% policy pass rate."
echo "============================================================"
