# Data Model: Policy Verification Framework

## Entities

### PolicyTestSuite
The top-level container for a group of related test cases.

| Field | Type | Description |
|-------|------|-------------|
| `version` | `str` | Schema version (e.g., "1.0") |
| `metadata` | `Metadata` | Suite metadata (name, owner, etc.) |
| `defaults` | `Optional[Dict]` | Shared attributes for all test cases in this suite |
| `test_cases` | `List[TestCase]` | List of individual verification tests |

### TestCase
A single verification requirement.

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique ID (e.g., "AI-001") |
| `name` | `str` | Human-readable description |
| `category` | `Enum` | `positive` or `negative` |
| `principal` | `Principal` | Simulated identity |
| `request` | `Request` | Capability and parameters |
| `expected` | `Expectation` | Expected outcome (Allowed, Policy, Audit Level) |
| `skip` | `bool` | Whether to skip this test |

### Principal
The identity making the request.

| Field | Type | Description |
|-------|------|-------------|
| `type` | `str` | `HUMAN`, `AI_AGENT`, `MACHINE` |
| `subject` | `str` | Identity identifier |
| `groups` | `List[str]` | Associated groups |
| `mfa_verified` | `bool` | MFA status |
| `request_ip` | `Optional[str]` | Originating IP |

### Expectation
The outcome to verify.

| Field | Type | Description |
|-------|------|-------------|
| `allowed` | `bool` | Expected Allow/Deny |
| `policy_matched` | `Optional[str]` | Expected policy name |
| `audit_level` | `Optional[str]` | Expected `BASIC` or `VERBOSE` |
| `reason_contains` | `Optional[str]` | Substring check for denial reason |
| `environments` | `Optional[Dict[str, bool]]` | Override `allowed` per environment |

## State Transitions
N/A (Read-only verification)

## Validation Rules
- All Test IDs in a suite must be unique.
- Negative tests MUST have an `expected.allowed = false`.
- If `expected.environments` is provided, it takes precedence over `expected.allowed`.
