# Implementation Plan: Backstage.io Governance Integration

**Branch**: `009-backstage-governance` | **Date**: 2026-02-02 | **Spec**: [specs/009-backstage-governance/spec.md](specs/009-backstage-governance/spec.md)
**Input**: Feature specification from `/specs/009-backstage-governance/spec.md`

## Summary

This feature implements a "read-only governance lens" for the HR AI Platform by integrating with Backstage.io. It delivers three key components:
1.  **Capability Catalog**: A build-time Python script (`scripts/generate-catalog.py`) that transforms the existing `index.yaml` into Backstage-compatible `catalog-info.yaml` files, grouped by domain, with embedded Mermaid diagrams for flows.
2.  **Policy Verification Dashboard**: An enhancement to the CI pipeline to generate a native Markdown verification report using `PolicyVerificationService` and publish it to Backstage TechDocs.
3.  **Audit Log Viewer**: A custom Backstage frontend plugin (React) and backend plugin (Node.js/TypeScript) to securely proxy and visualize audit logs from the `/audit/recent` endpoint, featuring filtering, anomaly highlighting, and admin-only CSV export.

## Technical Context

**Language/Version**: Python 3.11+ (Core/Scripts), TypeScript/Node.js 18+ (Backstage Plugins)
**Primary Dependencies**: 
- Python: `pydantic`, `pyyaml`, `jinja2` (for Markdown generation)
- Backstage: `@backstage/core-plugin-api`, `@backstage/backend-common`
**Storage**: Filesystem (Catalog/TechDocs), API Proxy (Audit Logs)
**Testing**: `pytest` (Python scripts), `jest` (Backstage plugins)
**Target Platform**: Linux (CI/CD), Backstage (Web)
**Project Type**: Hybrid (Python Scripts + TypeScript Plugins)
**Performance Goals**: Catalog generation < 5s; Audit log render < 2s for 10k entries.
**Constraints**: Backstage plugins must reside in `integrations/backstage/` to avoid polluting the Python root.
**Scale/Scope**: 13 initial capabilities, 107+ policy tests, ~10k audit logs/day.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Hexagonal Integrity**: The Catalog Generator acts as an Adapter (converting internal config to external format). The Audit Plugin is a completely separate Client.
- [x] **Actions vs Flows**: Correctly classified as a FLOW (multi-step integration and governance process).
- [x] **Python-Native**: Core governance logic remains in Python. The Backstage plugins are effectively external clients (TS required by platform).
- [x] **Observability**: The feature *is* an observability tool (Audit Log Viewer).
- [x] **Privacy & PII**: The Audit Viewer respects existing redaction; the CSV export is restricted to Admins (Article VIII).
- [x] **Development Standards**: Python scripts will use `pytest`; Plugins will use `jest`. TDD applies to both.
- [x] **Local Parity**: Catalog generation and Verification reporting can be run locally. Plugin development supports local `yarn dev`.

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
└── generate-catalog.py  # [NEW] Initiative 1

integrations/
└── backstage/           # [NEW] Initiative 3
    └── plugins/
        ├── audit-log/           # Frontend Plugin
        └── audit-log-backend/   # Backend Plugin

docs/
└── policy-verification/ # Target for Initiative 2
    └── latest.md        # [NEW] Generated Report
```

**Structure Decision**: We will place Backstage-specific code in `integrations/backstage/` to maintain the repository's primary identity as a Python Capability API while supporting the required TypeScript components for this integration.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| TypeScript/Node.js (Backstage) | Backstage plugin architecture requires it. | Cannot write Backstage plugins in Python. |