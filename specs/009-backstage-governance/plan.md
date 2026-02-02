# Implementation Plan: Backstage.io Governance Integration

**Branch**: `009-backstage-governance` | **Date**: 2026-02-02 | **Spec**: [specs/009-backstage-governance/spec.md](specs/009-backstage-governance/spec.md)
**Input**: Feature specification from `/specs/009-backstage-governance/spec.md`

## Summary

This feature implements a "read-only governance lens" for the HR AI Platform by integrating with Backstage.io. It delivers two key components:
1.  **Capability Catalog**: A build-time Python script (`scripts/generate_catalog.py`) that transforms the existing `index.yaml` into Backstage-compatible `catalog-info.yaml` files. It groups entities by domain, embeds Mermaid diagrams for flows, computes policy cross-references ("Governed By"), and links to the verification dashboard.
2.  **Policy Verification Dashboard**: An enhancement to the CI pipeline to generate a native Markdown verification report using `PolicyVerificationService` and publish it to Backstage TechDocs.

*Note: The Audit Log Viewer (Initiative 3) has been deferred. The existing `/audit/recent` endpoint is sufficient for current needs using standard visualization tools.*

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: `pydantic`, `pyyaml`, `jinja2` (for Markdown generation)
**Storage**: Filesystem (Catalog/TechDocs)
**Testing**: `pytest`
**Target Platform**: Linux (CI/CD)
**Project Type**: Python Scripts
**Performance Goals**: Catalog generation < 5s.
**Constraints**: None.
**Scale/Scope**: 13 initial capabilities, 107+ policy tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: The Catalog Generator acts as an Adapter (converting internal config to external format).
- [x] **Actions vs Flows**: Correctly classified as a FLOW (multi-step integration and governance process).
- [x] **Python-Native**: All logic is idiomatic Python.
- [x] **Observability**: N/A (Governance metadata generation).
- [x] **Privacy & PII**: N/A (Only metadata is processed).
- [x] **Development Standards**: Scripts will use `pytest`. TDD applies.
- [x] **Local Parity**: Catalog generation and Verification reporting can be run locally.

## Project Structure

### Documentation (this feature)

```text
specs/009-backstage-governance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output
    └── catalog-entity.yaml
```

### Source Code (repository root)

```text
config/
├── capabilities/        # Source of truth
│   └── index.yaml
└── policy-workday.yaml

scripts/
└── generate_catalog.py  # [NEW] Initiative 1

docs/
└── policy-verification/ # Target for Initiative 2
    └── latest.md        # [NEW] Generated Report
```

**Structure Decision**: Standard Python script layout. No new integrations directory required as the Backstage plugin initiative is deferred.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | | |