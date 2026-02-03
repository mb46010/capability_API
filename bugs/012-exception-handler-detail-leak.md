# BUG-012: Exception Details Leaked via HTTPException in Local Mode

## Severity
🟢 LOW

## Location
- **File(s)**: `src/api/routes/flows.py`
- **Line(s)**: 56-57

## Issue Description
The flow route handler catches all exceptions and re-raises them with the exception message in the detail:

```python
# ❌ POTENTIAL INFO LEAK
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

While the main.py exception handler sanitizes 500 errors in production, this pattern can still leak information:
1. The exception is logged with full detail before sanitization
2. If the exception handler fails, the raw message is exposed
3. In local/dev environments, full stack traces are exposed

Additionally, using a generic `str(e)` can expose:
- File paths
- Database connection strings
- Internal service URLs
- Stack trace information

## Impact
- **Information disclosure**: Internal implementation details leaked
- **Attack surface expansion**: Attackers learn about internal architecture
- **Compliance risk**: May expose PII if exception contains user data

## Root Cause
This is a common pattern that prioritizes debugging convenience over security. The general exception handler in main.py provides some protection, but defense-in-depth suggests sanitizing at the source.

## How to Fix

### Code Changes
Handle exceptions more specifically and sanitize before raising:

```python
# ✅ FIXED - Specific exception handling
from src.domain.exceptions import ConnectorError, ValidationError

@router.post("/{domain}/{flow}", ...)
async def start_flow(...):
    try:
        # ... flow start logic ...
    except HTTPException:
        raise  # Re-raise HTTP exceptions as-is
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ConnectorError as e:
        logger.error(f"Connector error in flow: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="Upstream service error")
    except Exception as e:
        logger.error(f"Unexpected error in flow: {e}", exc_info=True)
        # Don't expose the actual exception message
        raise HTTPException(
            status_code=500,
            detail="An internal error occurred. Please contact support."
        )
```

### Steps
1. Identify specific exception types that can occur
2. Handle each type with appropriate error message
3. Use logging to capture full details server-side
4. Return generic messages to clients for unexpected errors
5. Apply similar pattern to other routes

## Verification

### Test Cases
1. Cause an internal error (e.g., invalid connector config)
2. Verify response does not contain stack trace or internal paths
3. Verify error is logged with full details server-side

### Verification Steps
1. Trigger an error condition in flow creation
2. Inspect the API response
3. Check server logs for detailed error info

## Related Issues
- Related to overall error handling consistency

---
*Discovered: 2026-02-03*
