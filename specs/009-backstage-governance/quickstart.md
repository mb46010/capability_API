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

## 3. Developing the Backstage Plugin

The plugin code lives in `integrations/backstage/`.

**Prerequisites:**
- Node.js 18+
- Yarn

**Setup:**
```bash
cd integrations/backstage
yarn install
```

**Run Frontend Dev Server:**
```bash
cd plugins/audit-log
yarn start
```

**Run Backend Dev Server:**
```bash
cd plugins/audit-log-backend
yarn start
```
