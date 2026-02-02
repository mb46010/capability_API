# Research: Backstage.io Governance Integration

**Feature**: Backstage Governance Integration (`009-backstage-governance`)
**Date**: 2026-02-02

## 1. Catalog Generation Strategy

**Goal**: Transform `config/capabilities/index.yaml` (Pydantic models) into Backstage `catalog-info.yaml` entities.

### Decision
Use **Python + Jinja2 Templates**.
- **Rationale**: The `CapabilityRegistryService` already loads `index.yaml` into Pydantic models. We can reuse this logic and simply pass the models to a Jinja2 template to render the YAML output. This ensures the generator uses the exact same validation as the runtime API.
- **Alternatives**:
    - *Direct YAML Dump*: Using `PyYAML` to dump dictionaries. Rejected because Backstage YAML often requires specific formatting (comments, ordering) that is hard to control with raw dumpers.
    - *TypeScript Generator*: Writing the generator in TS. Rejected because it duplicates the `index.yaml` parsing logic which is already robust in Python.

## 2. Policy Verification Reporting

**Goal**: Publish policy test results to TechDocs.

### Decision
**Native Markdown Generation**.
- **Rationale**: TechDocs is based on MkDocs, which consumes Markdown. Generating HTML (as originally planned) creates integration issues (iframes, styling clashes). Generating Markdown ensures the report looks native to Backstage and is searchable.
- **Implementation**: `PolicyVerificationService` will add a `generate_markdown_report()` method, also using Jinja2.

## 3. Idempotency & CI

**Goal**: Ensure `catalog-info.yaml` is always in sync.

### Decision
**CI Check Script**.
- The CI pipeline will run `scripts/generate-catalog.py --check`.
- The script will generate the catalog in memory and compare it to disk. If diffs exist, it exits with non-zero code.
- This prevents "forgot to run generator" errors.