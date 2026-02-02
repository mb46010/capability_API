# Product Requirements Document — Backstage.io Governance Integration

**Capability Catalog | Policy Verification Dashboard | Audit Log Viewer**

HR AI Platform — Capability API

| Field | Value |
|-------|-------|
| Version | 1.0 |
| Date | February 1, 2026 |
| Status | Draft |
| Audience | Risk, Compliance, DPI, Engineering |
| Dependencies | Bug remediation complete (bugs 3–16), smoke test passing |

---

## 1. Executive Summary

The HR AI Platform's Capability API currently enforces policy-governed access control across three Workday domains (HCM, Time Management, Payroll). All policy definitions, capability metadata, and audit logs exist as structured data within the codebase. However, this governance posture is only visible to engineers who read YAML files and JSON logs. Non-technical stakeholders — risk, compliance, and DPI leadership — have no way to inspect or verify what the platform permits, denies, or records.

This PRD defines three Backstage.io integration initiatives that make the existing governance infrastructure **visible, browsable, and verifiable** without changing the underlying enforcement model. Backstage operates as a **read-only governance lens** over the existing YAML-in-Git workflow. No policy logic moves into Backstage; all enforcement remains in the Capability API's policy engine.

### Initiatives at a Glance

| # | Initiative | What It Delivers | Primary Audience |
|---|-----------|-----------------|-----------------|
| 1 | Capability Registry as Catalog | Browsable inventory of every capability with sensitivity, MFA requirements, domain grouping | Risk, DPI, Engineering |
| 2 | Policy Verification Dashboard | Interactive HTML report showing pass/fail of 107+ policy test scenarios | Compliance, Security, Audit |
| 3 | Audit Log Viewer | Filterable view of who did what, when, with what authorization | Compliance, Incident Response |

**What is deferred:** Policy change tracking (Initiative 4) is deferred. Policy YAML lives in Git, so every change already has a commit hash, author, timestamp, and diff. A Backstage plugin for this becomes necessary only when a second delivery mechanism (e.g., AWS CodePipeline) enters the picture and cross-system correlation is required.

---

## 2. Background and Context

### 2.1 Current Architecture

The Capability API uses a hexagonal (ports-and-adapters) architecture. The domain layer contains a policy engine that evaluates YAML-defined access policies at request time. A Workday simulator provides realistic HR data without connecting to production systems. Authentication is handled via a mock Okta provider issuing signed JWTs with configurable scopes, MFA claims, and principal types (HUMAN, MACHINE, AI_AGENT).

### 2.2 What Exists Today

- **Capability Registry:** `config/capabilities/index.yaml` — 13 capabilities across 3 domains, each with sensitivity level, MFA flag, domain, and tags.
- **Policy YAML:** `config/policy-workday.yaml` — declarative allow-list policies mapping principals to capabilities with conditions (MFA, TTL, scope, environment).
- **Policy Verification:** `PolicyVerificationService` runs 107+ scenario tests and generates an HTML report with pass/fail metrics, matched policies, and execution times.
- **Audit Logging:** Structured JSONL logs capturing actor, capability, policy matched, MFA status, token provenance, and PII-redacted parameters. Exposed via `/audit/recent` endpoint.
- **Security Metadata:** Every API response includes a security context block showing which policy granted access, audit level, MFA verification, and field filtering.

### 2.3 The Gap

All of the above is machine-readable but not human-browsable. A compliance officer today would need to: open a terminal, read YAML files, run a Python script, and parse JSON logs. Backstage closes this gap by providing a web interface over existing data, with zero changes to enforcement logic.

### 2.4 Design Principle

**Backstage is a lens, not a control plane.** All governance enforcement stays in the Capability API. Backstage reads from the same Git-committed YAML files and API endpoints. It cannot modify policies, approve access, or bypass controls. This separation ensures that the browsable view is always consistent with what the system actually enforces.

---

## 3. Initiative 1 — Capability Registry as Backstage Catalog

### 3.1 Objective

Enable any stakeholder to browse the complete inventory of platform capabilities, understand their sensitivity, see which require MFA, and navigate by domain — without reading YAML.

### 3.2 Data Source

The existing `config/capabilities/index.yaml` serves as the single source of truth. Each capability entry contains: id, name, domain, type (action/flow/composite), sensitivity (low/medium/high/critical), requires_mfa, tags, description, and an optional `implementation_flow` field containing a Mermaid diagram for composite capabilities. This file is already validated at startup by `CapabilityRegistryService`.

### 3.3 Backstage Entity Mapping

Each capability maps to a Backstage API entity. The `index.yaml` is transformed into `catalog-info.yaml` entries via a build-time generator script:

| index.yaml Field | Backstage Entity Field | Notes |
|-------------------|----------------------|-------|
| id | metadata.name | Dotted name becomes the entity identifier |
| name | metadata.title | Human-readable display name |
| description | metadata.description | Shown in catalog search results |
| domain | metadata.annotations[capability-api/domain] | Custom annotation for filtering |
| sensitivity | metadata.annotations[capability-api/sensitivity] | Drives visual badges |
| requires_mfa | metadata.annotations[capability-api/requires-mfa] | Drives MFA indicator |
| tags | metadata.tags | Direct mapping, enables tag-based filtering |
| type | spec.type | action or flow |
| implementation_flow | TechDocs embedded Mermaid block | Rendered as visual diagram on entity page; only present for composite capabilities |

### 3.4 Functional Requirements

**FR-CAT-01: Catalog Generator Script.** A build-time script (`scripts/generate-catalog.py`) reads `index.yaml` and produces Backstage-compatible `catalog-info.yaml` files. This runs in CI on every commit to `config/capabilities/`. The script is idempotent — running it twice produces identical output.

**FR-CAT-02: Domain Grouping.** Capabilities are grouped under Backstage System entities by domain. The catalog shows three systems: workday-hcm, workday-time, and workday-payroll. Each capability entity declares its parent system via `spec.system`.

**FR-CAT-03: Sensitivity Badges.** The Backstage UI shows visual indicators for sensitivity level (color-coded: green/yellow/orange/red for low/medium/high/critical) and an MFA-required badge where applicable. These are driven by custom annotations and rendered via a lightweight Backstage frontend plugin.

**FR-CAT-04: Cross-Reference to Policy.** Each capability entity page includes a "Governed By" section listing which policies reference this capability (including wildcard matches). This is computed by the generator script by parsing `policy-workday.yaml` and matching capability patterns.

**FR-CAT-05: Staleness Detection.** CI validates that `catalog-info.yaml` is in sync with `index.yaml`. If a capability is added or modified without regenerating catalog files, the pipeline fails with a clear diff.

**FR-CAT-06: Implementation Flow Diagrams.** Composite capabilities may include an optional `implementation_flow` field containing a Mermaid `graph TD` diagram describing the orchestration sequence and the atomic capabilities invoked at each step. When present, the generator script embeds the Mermaid block into the capability's TechDocs page. Backstage renders it as a visual flow diagram on the entity page. Atomic capabilities (all 13 current entries) omit this field — no diagram is rendered. Example:

```yaml
hr.onboarding.prepare_workspace:
  type: composite
  implementation_flow: |
    graph TD
      A[Get employee details] -->|workday.hcm.get_employee| B[Get manager]
      B -->|workday.hcm.get_manager_chain| C[Create Slack channel]
      C -->|slack.create_channel| D[Provision Google account]
      D -->|google.provision_account| E[Return workspace info]
  requires_capabilities:
    - workday.hcm.get_employee
    - workday.hcm.get_manager_chain
    - slack.create_channel
    - google.provision_account
```

**FR-CAT-07: Flow-to-Capability Validation.** When `implementation_flow` is present, CI validates that every capability name referenced in the Mermaid edge labels matches an entry in `requires_capabilities`, and vice versa. Mismatches fail the pipeline with a clear diff showing which references are missing or extraneous. This ensures the visual diagram stays in sync with the declared dependency list.

### 3.5 User Stories

- **As a risk officer,** I want to browse all capabilities tagged "pii" so I can verify each one has appropriate sensitivity classification.
- **As a DPI lead,** I want to see which capabilities require MFA so I can confirm alignment with our data protection standards.
- **As an engineer,** I want to check what policies govern a capability I'm adding so I can write the correct test scenarios.
- **As an engineer using an AI coding assistant,** I want the assistant to read the `implementation_flow` diagram for a composite capability so it can generate the correct orchestration logic for the MCP tool function.

### 3.6 Acceptance Criteria

- **AC-01:** All 13 capabilities appear in Backstage catalog with correct metadata.
- **AC-02:** Filtering by domain, sensitivity, or tag returns correct results.
- **AC-03:** Each capability page shows its governing policies.
- **AC-04:** Adding a new capability to `index.yaml` and running the generator produces a valid catalog entry.
- **AC-05:** CI fails if `catalog-info.yaml` is stale relative to `index.yaml`.
- **AC-06:** A composite capability with `implementation_flow` renders a Mermaid diagram on its Backstage entity page.
- **AC-07:** CI fails if capability names in a Mermaid flow diagram don't match `requires_capabilities`.

---

## 4. Initiative 2 — Policy Verification Dashboard

### 4.1 Objective

Give compliance and security stakeholders a web-accessible, always-current view of whether the platform's access policies behave as intended — without running scripts or reading test output.

### 4.2 Data Source

The `PolicyVerificationService` already runs 107+ test scenarios defined in `tests/policy/scenarios/` and produces a `VerificationReport` object. The existing `generate_html_report()` function renders this as a standalone HTML file with summary metrics, pass/fail badges, matched policies, and execution times.

### 4.3 Integration Approach: TechDocs

The HTML report is published as a Backstage TechDocs page attached to the Capability API's service entity. This approach has the lowest integration cost because TechDocs is a built-in Backstage feature that renders static content — no custom plugin required.

How it works:

1. **CI runs verification:** On every commit to `config/policy-workday.yaml` or `tests/policy/scenarios/`, the CI pipeline executes the policy verifier and generates the HTML report.
2. The report is placed in `docs/policy-verification/latest.html` within the repo.
3. Backstage TechDocs picks up the file via `mkdocs.yml` configuration and publishes it.
4. Stakeholders access it at the Capability API's TechDocs tab in Backstage.

### 4.4 Functional Requirements

**FR-PVD-01: CI-Generated Report.** The GitHub Actions workflow runs the policy verifier on every PR that modifies policy YAML or test scenarios. The report is committed to the `docs/` directory. PRs that introduce policy verification failures are blocked.

**FR-PVD-02: Report Content.** The HTML report includes the following sections, all of which already exist in the current template: summary metrics (total tests, passed, failed, pass rate); failed tests table (test ID, name, expected vs. actual result, error message) displayed prominently at the top when failures exist; full results table (every test case with result badge, matched policy name, execution time); and timestamp and version (when the report was generated and against which policy file).

**FR-PVD-03: TechDocs Configuration.** A `mkdocs.yml` is added to the repository root. The policy verification report is listed under a "Governance" nav section. Additional TechDocs pages may include the developer guide for adding capabilities and the security requirements mapping.

**FR-PVD-04: Link from Catalog Entities.** Each capability entity in the catalog (from Initiative 1) includes a link to the verification dashboard, making it easy to navigate from "what exists" to "is it correctly governed."

### 4.5 User Stories

- **As a compliance officer,** I want to see the current pass rate of policy tests so I can confirm all access rules are working as intended before a quarterly review.
- **As a security reviewer,** I want to see which specific tests failed so I can assess whether a policy change introduced a regression.
- **As an auditor,** I want a timestamped report I can reference in audit findings without needing to run any tools.

### 4.6 Acceptance Criteria

- **AC-01:** Policy verification report is accessible via Backstage TechDocs at the Capability API's service page.
- **AC-02:** Report updates automatically on every merge to main that touches policy or scenario files.
- **AC-03:** PRs that introduce verification failures are blocked from merging.
- **AC-04:** Report timestamp matches the most recent CI run.
- **AC-05:** Report renders correctly in Backstage (no broken styles, all tables readable).

---

## 5. Initiative 3 — Audit Log Viewer

### 5.1 Objective

Provide compliance and incident response teams with a browsable, filterable view of every action executed through the Capability API — who did what, when, under what authorization, and what was the outcome.

### 5.2 Data Source

The Capability API already exposes a `/audit/recent` endpoint returning structured JSONL entries. Each entry includes: timestamp, actor, acting_through (MCP vs. direct), capability, policy_matched, mfa_verified, token provenance (type, scope, TTL, issued_at, expires_at, auth_age_seconds), result, and PII-redacted parameters.

### 5.3 Integration Approach: Custom Backstage Plugin

Unlike Initiatives 1 and 2 which use built-in Backstage features, the audit log viewer requires a lightweight custom frontend plugin. This is because audit data is dynamic (not static content) and requires filtering, sorting, and pagination that TechDocs cannot provide.

### 5.4 Functional Requirements

**FR-AUD-01: Audit API Proxy.** The Backstage backend proxies requests to the Capability API's `/audit/recent` endpoint. This keeps the Capability API's network boundary intact — Backstage never accesses audit logs directly. Proxy configuration is added to Backstage's `app-config.yaml`.

**FR-AUD-02: Filterable Log Table.** The plugin renders a table with the following columns and filter capabilities:

| Column | Filter Type | Description |
|--------|------------|-------------|
| Timestamp | Date range picker | When the action was executed |
| Actor | Text search | Principal ID (e.g., EMP001, agent-assistant@local.test) |
| Capability | Dropdown (from catalog) | Which capability was invoked |
| Policy Matched | Dropdown | Which policy granted or denied access |
| Result | Toggle (success/denied/error) | Outcome of the action |
| MFA Verified | Toggle (yes/no) | Whether MFA was present on the token |
| Acting Through | Dropdown (direct/mcp) | Whether the call came through MCP or direct API |
| Token TTL | Range slider | Token lifetime in seconds |

**FR-AUD-03: Event Detail Drawer.** Clicking a row opens a side drawer showing the full audit entry, including token provenance chain (original_token_id linking to parent), auth_age_seconds, scope list, and the redacted parameter payload. Sensitive fields are marked with a "PII Redacted" badge.

**FR-AUD-04: Anomaly Highlighting.** The table visually highlights entries that may warrant attention:

- **Denied requests:** Red row background.
- **High auth_age_seconds:** Orange indicator when authentication age exceeds the policy's max_auth_age_seconds.
- **Short-lived token accessing sensitive data:** Yellow indicator when TTL is under 60s and sensitivity is high or critical.
- **Unusual hours:** Gray indicator for requests outside business hours (configurable).

**FR-AUD-05: Export.** A CSV export button allows compliance teams to download the currently filtered view for inclusion in audit reports or regulatory filings.

**FR-AUD-06: Pagination.** The viewer supports cursor-based pagination. The `/audit/recent` endpoint already accepts limit and offset parameters. The plugin loads 50 entries per page with infinite scroll or explicit page navigation.

### 5.5 User Stories

- **As a compliance officer,** I want to filter audit logs by "denied" results so I can investigate unauthorized access attempts.
- **As an incident responder,** I want to search by actor to see all actions a specific principal took in a time window.
- **As a DPI lead,** I want to see all accesses to payroll data (high-sensitivity capabilities) to verify MFA was enforced on each one.
- **As an auditor,** I want to export a filtered log to CSV for inclusion in a compliance report.

### 5.6 Acceptance Criteria

- **AC-01:** Audit log viewer is accessible from the Capability API's service page in Backstage.
- **AC-02:** All filter types function correctly and can be combined.
- **AC-03:** Event detail drawer shows full token provenance chain.
- **AC-04:** Anomaly highlighting correctly identifies denied requests and stale tokens.
- **AC-05:** CSV export produces a valid file containing the currently filtered dataset.
- **AC-06:** Plugin loads in under 2 seconds for datasets up to 10,000 entries.

---

## 6. Cross-Cutting Concerns

### 6.1 Authentication and Authorization

Backstage access is gated by the organization's existing identity provider. The Capability API's `/audit/recent` endpoint requires admin-group membership (hr-platform-admins). The Backstage backend proxy inherits this check. Catalog and TechDocs content is read-only and available to any authenticated Backstage user.

### 6.2 Data Flow

All three initiatives follow the same principle: data originates in the Capability API's Git-committed config or runtime logs and flows one-way into Backstage for display. Backstage never writes back. This ensures the displayed state cannot diverge from the enforced state.

| Initiative | Data Origin | Transport | Backstage Feature |
|-----------|------------|-----------|-------------------|
| Capability Catalog | config/capabilities/index.yaml | CI-generated catalog-info.yaml committed to repo | Software Catalog (built-in) |
| Policy Verification | tests/policy/scenarios/ + policy YAML | CI-generated HTML report in docs/ | TechDocs (built-in) |
| Audit Log Viewer | /audit/recent API endpoint | Runtime proxy from Backstage backend | Custom frontend plugin |

### 6.3 Failure Modes

- **Catalog stale:** CI detects drift between index.yaml and catalog-info.yaml. Pipeline fails, blocking merge. Self-healing.
- **Verification report stale:** Same CI gate. If policy changes without passing verification, the report is not updated and the merge is blocked.
- **Audit API down:** The Backstage plugin shows a "Service Unavailable" banner with a retry button. No data loss — audit logs continue writing to disk.
- **Backstage down:** Zero impact on enforcement. The Capability API continues enforcing policies, logging audits, and serving requests. Governance visibility is degraded until Backstage recovers.

### 6.4 Future AWS CI/CD Compatibility

All three initiatives use GitHub-based CI today. The catalog generator script and policy verifier are plain Python scripts with no GitHub-specific dependencies — they can run in AWS CodeBuild, CodePipeline, or any CI environment. The audit log viewer's proxy configuration is Backstage-native and infrastructure-agnostic. No initiative creates a hard dependency on GitHub.

---

## 7. Implementation Roadmap

**Prerequisite:** All critical bugs from the code audit (bugs 3–16) are resolved and the end-to-end smoke test passes.

| Phase | Initiative | Deliverables | Effort | Dependencies |
|-------|-----------|-------------|--------|-------------|
| Phase 1 | Capability Catalog | Generator script, catalog-info.yaml, CI validation, Backstage entity registration | 3–4 days | Bug fixes complete, Backstage instance running |
| Phase 2 | Policy Verification Dashboard | mkdocs.yml, CI pipeline update, TechDocs publishing | 2–3 days | Phase 1 (service entity exists for TechDocs attachment) |
| Phase 3 | Audit Log Viewer | Backstage proxy config, frontend plugin (React), anomaly highlighting, CSV export | 5–7 days | Phase 2 (catalog provides capability dropdown data) |

**Total estimated effort:** 10–14 working days from a single engineer, assuming Backstage instance setup is already complete.

**Recommended staffing:** One engineer with Backstage plugin experience (Phases 1–2 can be done by any backend engineer; Phase 3 requires React/Backstage frontend familiarity).

---

## 8. Success Metrics

| Metric | Target | How Measured |
|--------|--------|-------------|
| Catalog completeness | 100% of capabilities visible in Backstage | Count of catalog entities vs. index.yaml entries |
| Catalog accuracy | Zero drift between index.yaml and catalog | CI validation pass rate |
| Verification visibility | Report accessible without terminal access | Stakeholder can navigate to report in <3 clicks from Backstage home |
| Verification currency | Report reflects latest policy state | Report timestamp within 1 hour of last policy merge |
| Audit query time | Filter + render in <2 seconds | Frontend performance measurement on 10K entry dataset |
| Audit coverage | 100% of API actions appear in viewer | Compare audit log entry count vs. API request count over a test period |
| Stakeholder adoption | ≥3 non-engineering users access Backstage weekly | Backstage access logs after initial rollout |

---

## 9. Risks and Mitigations

| Risk | Severity | Likelihood | Mitigation |
|------|----------|-----------|------------|
| Backstage setup complexity delays all three initiatives | High | Medium | Phases 1–2 can be partially validated without a running Backstage instance (catalog-info.yaml and HTML report are testable artifacts). Phase 3 requires Backstage. |
| Audit log volume exceeds /audit/recent endpoint capacity | Medium | Low (demo scale) | Current JSONL-based storage is sufficient for demo. For production, migrate to a database-backed audit store with indexed queries. The Backstage plugin's proxy layer is unchanged. |
| Custom plugin maintenance burden | Medium | Medium | Only Initiative 3 requires a custom plugin. Keep it minimal — table, filters, drawer, export. No custom state management or complex UX. |
| Stakeholders expect Backstage to enforce policy (not just display) | High | Medium | Documentation and onboarding explicitly state Backstage is read-only. The "Governed By" section on each entity reinforces that policy lives in YAML, not in the UI. |
| Catalog generator falls out of sync with index.yaml schema changes | Low | Medium | Generator script validates against the same Pydantic schema used by CapabilityRegistryService. Schema changes break both the API and the generator simultaneously. |

---

## 10. Appendices

### A. Capability Registry Schema (index.yaml)

Each capability entry in `config/capabilities/index.yaml` uses the following fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | string | Yes | Unique dotted identifier (e.g., workday.hcm.get_employee) |
| name | string | Yes | Human-readable display name |
| domain | string | Yes | Domain.subdomain grouping (e.g., workday.hcm) |
| type | enum | Yes | action \| flow \| composite |
| sensitivity | enum | Yes | low \| medium \| high \| critical |
| requires_mfa | boolean | No | Defaults to false |
| tags | string[] | No | Classification labels for filtering |
| description | string | No | Detailed description |
| deprecated | boolean | No | Defaults to false |
| implementation_flow | string (Mermaid) | No | Mermaid `graph TD` diagram describing orchestration for composite capabilities. Omit for atomic actions. |
| requires_capabilities | string[] | No | List of atomic capability IDs invoked by a composite capability. Must match references in `implementation_flow`. |

### B. Audit Log Entry Schema

Each entry in the JSONL audit log and `/audit/recent` response contains:

| Field | Type | Description |
|-------|------|-------------|
| timestamp | ISO 8601 | When the action was executed |
| actor | string | Principal ID |
| acting_through | string \| null | "mcp-server" or null for direct access |
| capability | string | Capability that was invoked |
| policy_matched | string \| null | Policy name that granted/denied access |
| result | string | success \| denied \| error |
| mfa_verified | boolean | Whether MFA was present |
| token_type | string | original \| exchanged |
| token_scope | string[] | Scopes on the token |
| token_ttl_seconds | integer | Token lifetime |
| auth_age_seconds | integer | Seconds since last authentication |
| original_token_id | string \| null | Parent token ID for exchange chains |

### C. Glossary

| Term | Definition |
|------|-----------|
| Capability | A single, named operation the platform can perform (e.g., get_employee, request_time_off) |
| Policy | A YAML-defined rule mapping principals to capabilities with optional conditions |
| Principal | An authenticated identity — HUMAN, MACHINE, or AI_AGENT — identified by JWT claims |
| MFA | Multi-Factor Authentication; verified via the "amr" claim in the JWT |
| Sensitivity | Data classification level (low/medium/high/critical) driving audit and MFA requirements |
| TechDocs | Backstage's built-in documentation publishing feature, rendering static content from Git |
| Token Exchange | The process of swapping a user's original JWT for a scoped, short-lived token (e.g., for MCP) |

---

*End of document.*