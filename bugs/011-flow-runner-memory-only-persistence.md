# BUG-011: Flow Runner Uses In-Memory Storage Only

## Severity
🟢 LOW

## Location
- **File(s)**: `src/adapters/filesystem/local_flow_runner.py`
- **Line(s)**: 6-9

## Issue Description
The `LocalFlowRunnerAdapter` stores all flow execution state in memory only:

```python
# ❌ NO PERSISTENCE - Data lost on restart
class LocalFlowRunnerAdapter(FlowRunnerPort):
    def __init__(self):
        # In-memory store for MVP. For persistence, this should write to a file/DB.
        self._executions: Dict[str, Dict[str, Any]] = {}
```

This means:
1. All running flows are lost on application restart
2. Flow status queries return 404 after restart
3. Long-running HR workflows (onboarding, offboarding) cannot survive deployments

The comment acknowledges this is for MVP, but it represents a significant limitation.

## Impact
- **Data loss on restart**: All in-flight flows are lost
- **Broken workflows**: HR processes that span hours/days cannot complete
- **Poor user experience**: Users see "flow not found" after any deployment
- **Audit gap**: No persistent record of flow executions

## Root Cause
This is intentional technical debt for MVP/prototype phase. The implementation prioritizes simplicity over durability. However, for an HR platform dealing with critical workflows like onboarding and offboarding, this represents a significant gap.

## How to Fix

### Code Changes
Add file-based or database persistence:

```python
# ✅ FIXED - File-based persistence
import json
from pathlib import Path

class LocalFlowRunnerAdapter(FlowRunnerPort):
    def __init__(self, storage_path: str = "data/flows"):
        self._storage_path = Path(storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        self._executions = self._load_all()

    def _load_all(self) -> Dict[str, Dict[str, Any]]:
        executions = {}
        for file in self._storage_path.glob("*.json"):
            with open(file) as f:
                data = json.load(f)
                executions[data["flow_id"]] = data
        return executions

    def _persist(self, flow_id: str, data: Dict[str, Any]):
        file_path = self._storage_path / f"{flow_id}.json"
        with open(file_path, "w") as f:
            json.dump(data, f)

    async def start_flow(self, domain, flow, params, principal_id) -> str:
        flow_id = str(uuid.uuid4())
        execution = {
            "flow_id": flow_id,
            # ... other fields
        }
        self._executions[flow_id] = execution
        self._persist(flow_id, execution)  # Persist to disk
        return flow_id
```

### Steps
1. Create a `data/flows/` directory for flow state storage
2. Update `LocalFlowRunnerAdapter` to write flow state to JSON files
3. Load existing flows on startup
4. Add cleanup for completed/expired flows
5. Consider SQLite or a proper database for production

## Verification

### Test Cases
1. Start a flow, restart the application, query flow status - should return the flow
2. Verify flow state files are created in the storage directory
3. Test concurrent flow creation

### Verification Steps
1. Start a flow
2. Restart the application
3. Query the flow by ID
4. Verify status is preserved

## Related Issues
- Related to overall production-readiness of the MVP

---
*Discovered: 2026-02-03*
