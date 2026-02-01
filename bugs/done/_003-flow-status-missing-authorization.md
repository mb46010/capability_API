# BUG-003: Flow status can be accessed without authorization checks

## Severity
🟠 HIGH

## Location
- **File(s)**: src/domain/services/flow_service.py
- **Line(s)**: 48-65

## Issue Description
`FlowService.get_status` returns flow status data for any authenticated caller without checking whether the caller is the owner of the flow or authorized by policy. Flow IDs are UUIDs but still effectively act as bearer tokens; any user who obtains a flow ID can query its status and results.

## Impact
- Information disclosure across tenants/users (IDOR risk).
- Exposure of workflow results or error details to unauthorized principals.

## Root Cause
The flow status path lacks a policy check and does not tie flow IDs to principals.

## How to Fix

### Code Changes
- Persist `principal_id` (and optionally groups/type) with flow executions in the flow runner adapter.
- In `get_status`, verify the requesting principal matches the owner or is authorized by policy.
- Alternatively introduce a dedicated policy capability (e.g., `workday.flow_status`) and evaluate against it.

### Steps
1. Update `FlowRunnerPort` and `LocalFlowRunnerAdapter` to store owner metadata.
2. Pass principal info when starting a flow.
3. Enforce ownership or policy check before returning status.
4. Add tests for unauthorized access.

## Verification

### Test Cases
- Caller A starts a flow; Caller B attempts `GET /flows/{id}` → 403.
- Admin (or authorized role) can read status if policy allows.

### Verification Steps
1. Start a flow as user A and store flow ID.
2. Request status as user B → expect 403.
3. Request status as user A → expect 200.

## Related Issues
None.

---
*Discovered: 2026-02-01*
