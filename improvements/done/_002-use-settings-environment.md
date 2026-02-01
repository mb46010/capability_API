# 002: Use settings.ENVIRONMENT consistently

## Impact
**Effort**: Low (1 hour) | **Impact**: Medium | **Priority**: 2

## Location
- **File(s)**: src/api/routes/actions.py, src/api/routes/flows.py
- **Component/Module**: API route handlers

## Current State
Routes read `ENVIRONMENT` directly from `os.getenv` while the rest of the app uses validated `settings.ENVIRONMENT`. This can lead to mismatches if `.env` or settings validation normalizes values.

## Proposed Improvement
Replace direct `os.getenv("ENVIRONMENT", "local")` reads in routes with `settings.ENVIRONMENT` for consistency and centralized validation.

## Benefits
- Eliminates configuration drift between routes and app settings.
- Ensures only allowed environment values are used.
- Simplifies future changes to environment handling.

## Implementation

### Approach
Import `settings` from `src.lib.config_validator` in route modules and use it instead of `os.getenv`.

### Estimated Effort
1 hour.

### Steps
1. Remove `os` usage for environment in route handlers.
2. Replace `environment = os.getenv(...)` with `environment = settings.ENVIRONMENT`.
3. Run quick smoke tests for action/flow endpoints.

## Example

### Before
```python
environment = os.getenv("ENVIRONMENT", "local")
```

### After
```python
from src.lib.config_validator import settings

environment = settings.ENVIRONMENT
```

## Considerations
- Ensure route modules do not trigger side effects on import (settings already loads at startup).

## Related Improvements
- 003-docs-quickstart-alignment.md

---
*Identified: 2026-02-01*
