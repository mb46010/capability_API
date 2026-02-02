# BUG-010: Uvicorn Reload Mode Enabled in Production

## Severity
🟢 LOW

## Location
- **File(s)**: `src/main.py`
- **Line(s)**: 197-203

## Issue Description
The main entry point runs uvicorn with `reload=True` unconditionally:

```python
if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # ❌ Always enabled, even in production
    )
```

While this is convenient for development, running with reload in production:
1. Adds unnecessary overhead (file watching)
2. Could cause unexpected restarts if files change
3. May expose development-only behavior

## Impact
- **Performance Overhead**: File system watcher runs continuously
- **Instability**: File changes (logs, temp files) could trigger unintended restarts
- **Security**: Reload mode may have different error handling or debugging features enabled

## Root Cause
The entry point was written for development convenience without environment-aware configuration.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Environment-aware uvicorn configuration
if __name__ == "__main__":
    is_development = settings.ENVIRONMENT in ["local", "dev"]

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=is_development,  # Only in dev environments
        workers=1 if is_development else 4,  # Multi-worker in prod
        log_level="debug" if is_development else "info"
    )
```

### Alternative: Use environment variable
```python
# ✅ FIXED: Explicit control via environment
import os

if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("UVICORN_RELOAD", "false").lower() == "true",
        workers=int(os.getenv("UVICORN_WORKERS", "1"))
    )
```

### Steps
1. Make reload mode conditional on environment
2. Consider removing the `if __name__ == "__main__"` block entirely for production (use uvicorn CLI or process manager)
3. Document recommended production startup command

## Verification

### Test Cases
1. In local environment, reload should be enabled
2. In prod environment, reload should be disabled
3. Verify application still starts correctly in both modes

### Verification Steps
```bash
# Check that production doesn't use reload
ENVIRONMENT=prod python -c "
from src.lib.config_validator import settings
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Should reload: {settings.ENVIRONMENT in [\"local\", \"dev\"]}')"
```

## Related Issues
- None

---
*Discovered: 2026-02-01*
