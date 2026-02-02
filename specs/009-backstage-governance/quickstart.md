# Quickstart: Backstage Governance Integration

## 1. Generating the Catalog

To transform `index.yaml` into Backstage catalog files:

```bash
# From repository root
python3 scripts/generate-catalog.py
```

This will output YAML files to `catalog/`.

**Verify output:**
```bash
ls -R catalog/
```

**Run in CI Mode (Check for diffs):**
```bash
python3 scripts/generate-catalog.py --check
```

## 2. Generating Policy Verification Report

Run the verification suite to produce the TechDocs report:

```bash
# Runs tests and generates docs/policy-verification/latest.md
pytest tests/policy/integration/test_policy_verification.py
```

View the report (requires MkDocs):
```bash
mkdocs serve
# Open browser to http://localhost:8000/policy-verification/latest/
```