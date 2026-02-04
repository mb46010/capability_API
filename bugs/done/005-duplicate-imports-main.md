# BUG-005: Duplicate Imports in main.py

## Severity
🟢 LOW

## Location
- **File(s)**: `src/main.py`
- **Line(s)**: 206-211

## Issue Description
The main application file contains duplicate imports that indicate copy-paste errors or incomplete refactoring:

```python
# ❌ PROBLEMATIC - Duplicate imports
from fastapi import Depends  # Line 207
from fastapi import Depends  # Line 208 - Duplicate!
from src.domain.ports.connector import ConnectorPort
from src.domain.services.policy_engine import PolicyEngine
from src.api.dependencies import get_policy_engine, get_connector
```

While Python handles duplicate imports gracefully (they're essentially no-ops), this indicates:
1. Poor code hygiene
2. Possible incomplete refactoring
3. Potential for confusion during maintenance

The comment `# ... (previous code)` on line 213 also suggests incomplete code or documentation.

## Impact
- **Code maintainability**: Confusing for developers
- **Technical debt**: Indicates rushed or incomplete changes
- **No runtime impact**: Python handles duplicates gracefully

## Root Cause
Copy-paste error or incomplete merge/refactoring. The imports near the health check endpoint appear to have been added separately from the imports at the top of the file.

## How to Fix

### Code Changes
Remove duplicate imports and consolidate at the top:

```python
# ✅ FIXED - Clean imports at top of file
from fastapi import FastAPI, Request, HTTPException, Depends
from typing import Union
# ... other imports

# Remove the duplicates near line 207-208
# Remove the "# ... (previous code)" comment
```

### Steps
1. Open `src/main.py`
2. Remove the duplicate `from fastapi import Depends` statements at lines 207-208
3. Verify `Depends` is already imported at the top of the file
4. Remove the `# ... (previous code)` comment on line 213
5. Run linter/formatter to ensure clean imports

## Verification

### Test Cases
1. Run `python -m py_compile src/main.py` - should succeed
2. Run the application and verify health endpoint works
3. Run `ruff check src/main.py` - should pass

### Verification Steps
1. Apply the fix
2. Run the test suite
3. Verify application starts correctly

## Related Issues
- None

---
*Discovered: 2026-02-03*
