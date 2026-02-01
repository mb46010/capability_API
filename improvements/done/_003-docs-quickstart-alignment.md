# 003: Align quickstart and onboarding docs

## Impact
**Effort**: Low (1-2 hours) | **Impact**: Medium | **Priority**: 2

## Location
- **File(s)**: README.md, docs/onboarding.md
- **Component/Module**: Documentation

## Current State
Quickstart and onboarding show different run commands (`python src/main.py` vs `python -m src.main`) and do not mention environment flags like `ENABLE_DEMO_RESET`. Test guidance defaults to full `pytest`, which can be slow for contributors.

## Proposed Improvement
Normalize run commands, add a short environment/config section, and add a recommended fast test path (unit-only) before full integration tests.

## Benefits
- Reduces onboarding confusion and setup drift.
- Improves developer productivity with clearer test guidance.
- Makes demo/reset behavior discoverable.

## Implementation

### Approach
Update README and onboarding to share a single canonical run command and a short "Environment Flags" section.

### Estimated Effort
1-2 hours.

### Steps
1. Pick a single run command (recommend `python -m src.main`).
2. Add a short section covering `ENVIRONMENT`, `POLICY_PATH`, and `ENABLE_DEMO_RESET`.
3. Add a "Quick Tests" subsection with `pytest tests/unit/` then full suite.

## Example

### Before
```markdown
# README
python src/main.py

# docs/onboarding.md
python -m src.main
```

### After
```markdown
# README and docs/onboarding.md
python -m src.main

### Environment Flags
- ENVIRONMENT: local|dev|prod|test
- POLICY_PATH: config/policy-workday.yaml
- ENABLE_DEMO_RESET: true|false (local only)

### Quick Tests
pytest tests/unit/
```

## Considerations
- Keep docs in sync by referencing a shared snippet or linking to onboarding from README.

## Related Improvements
- 002-use-settings-environment.md

---
*Identified: 2026-02-01*
