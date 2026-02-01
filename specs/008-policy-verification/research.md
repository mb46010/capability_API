# Research: Policy Verification Framework

## Decisions

### Decision 1: JUnit XML Format
**Selection**: Standard JUnit XML (Jenkins/XUnit compatible).
**Rationale**: Most GitHub Actions (e.g., `EnricoMi/publish-unit-test-result-action`) expect the standard format with `<testsuites>`, `<testsuite>`, and `<testcase>` elements.
**Alternatives considered**: TAP (Test Anything Protocol) - rejected as JUnit XML has better UI integration in CI.

### Decision 2: Report Generation with Jinja2
**Selection**: Single-file standalone HTML using Jinja2.
**Rationale**: Stakeholders need a portable report that doesn't require a web server or external CSS/JS dependencies (using inline CSS).
**Alternatives considered**: Static site generators (Hugo/MkDocs) - rejected as too heavy for a single report.

### Decision 3: Pydantic Model Structure
**Selection**: Pydantic V2 with `RootModel` or `Discriminators` for Principal types.
**Rationale**: Allows strict validation of principal-specific fields (e.g., `agent_id` for AI agents vs `subject` for humans).
**Alternatives considered**: Flat dictionaries - rejected as they violate Article II (Data Contracts).

### Decision 4: Git Hook Implementation
**Selection**: Shell script wrapper for the CLI tool.
**Rationale**: Simplest integration with `.git/hooks/pre-commit`. Using `git diff` to filter files ensures fast commits when policies aren't touched.
**Alternatives considered**: Pre-commit framework (`pre-commit.com`) - rejected to avoid extra tool dependency for a core security requirement.

## Best Practices

- **Security**: Scenarios MUST be treated as sensitive but non-secret. They define policy requirements.
- **TDD**: Verification logic MUST be tested using a "Mock Policy Engine" or a fixed "Reference Policy" to ensure the framework itself is correct before testing real policies.
- **Article VIII**: Principal IDs in test scenarios should be realistic but synthetic (e.g., `agent-007@test.internal`) to avoid PII in repositories.
