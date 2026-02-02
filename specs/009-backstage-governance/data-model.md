# Data Model: Backstage Governance Integration

## 1. Backstage Entities (Target Model)

The generator transforms internal `Capability` objects into these Backstage entities.

### System: Domain
Represents a functional domain (e.g., HCM, Payroll).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `apiVersion` | string | `backstage.io/v1alpha1` | Static |
| `kind` | string | `System` | Static |
| `metadata.name` | string | e.g., `workday-hcm` | Derived from `domain` |
| `metadata.title` | string | e.g., "Workday HCM" | Formatted `domain` |
| `spec.owner` | string | `platform-engineering` | Static (for now) |

### API: Capability
Represents a specific Capability (Action or Flow).

| Field | Type | Description | Source |
|-------|------|-------------|--------|
| `apiVersion` | string | `backstage.io/v1alpha1` | Static |
| `kind` | string | `API` | Static |
| `metadata.name` | string | `workday.hcm.get_employee` | `id` |
| `metadata.title` | string | "Get Employee" | `name` |
| `metadata.description` | string | Description text | `description` |
| `metadata.tags` | list[str] | Classification tags | `tags` |
| `metadata.links` | list[Link] | Links to dashboard | Generated |
| `metadata.annotations` | dict | Custom metadata | Mapped fields |
| `spec.type` | string | `action` or `flow` | `type` |
| `spec.system` | string | `workday-hcm` | `domain` |
| `spec.lifecycle` | string | `production` | Static |
| `spec.definition` | string | OpenAPI or AsyncAPI | Placeholder |

#### Custom Annotations
| Annotation | Source Field | Example |
|------------|--------------|---------|
| `capability-api/domain` | `domain` | `workday.hcm` |
| `capability-api/sensitivity` | `sensitivity` | `high` |
| `capability-api/requires-mfa` | `requires_mfa` | `true` |
| `capability-api/governed-by` | `policy_matched` | `policy-workday.yaml` (policies listing this capability) |

#### Links
| Title | URL | Icon |
|-------|-----|------|
| Policy Verification | `/docs/default/component/capability-api/governance` | `dashboard` |

## 2. Policy Verification Report (Source Model)

The `PolicyVerificationService` produces this internal model, which is rendered to Markdown.

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | datetime | Run time |
| `policy_version` | string | Hash of policy file |
| `total_tests` | int | Count of scenarios |
| `passed_tests` | int | Count passed |
| `failed_tests` | int | Count failed |
| `results` | list[TestResult] | Detailed outcomes |

### TestResult
| Field | Type | Description |
|-------|------|-------------|
| `scenario_id` | string | Unique test ID |
| `description` | string | What was tested |
| `outcome` | enum | `pass`, `fail`, `error` |
| `matched_policy` | string | Policy that triggered |
| `duration_ms` | float | Execution time |
