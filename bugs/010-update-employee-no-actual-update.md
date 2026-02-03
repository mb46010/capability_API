# BUG-010: update_employee Does Not Actually Update Employee Data

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/services/hcm.py`
- **Line(s)**: 227-266

## Issue Description
The `update_employee` function records change information but never actually applies the updates to the employee object:

```python
# ❌ BUG - Changes recorded but never applied
async def update_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # ... validation ...

    changes = []
    for key, value in updates.items():
        if hasattr(employee, key):
            old_val = getattr(employee, key)
            changes.append({
                "field": key,
                "old_value": str(old_val),
                "new_value": str(value)
            })
            # ❌ MISSING: setattr(employee, key, value)
            # The comment says "For HCM core updates, they usually go to
            # PENDING_APPROVAL status" but there's no workflow mechanism

    return {
        "employee_id": employee_id,
        "status": "PENDING_APPROVAL",  # Returns PENDING but nothing happens
        "changes": changes,
        # ...
    }
```

The function:
1. Records what changes would be made
2. Returns `PENDING_APPROVAL` status
3. Never actually queues or applies the changes

This differs from `update_contact_info` which DOES apply changes immediately.

## Impact
- **Silent data loss**: Updates appear successful but are silently discarded
- **Misleading response**: API returns success with changes listed, but nothing changes
- **Inconsistent behavior**: `update_contact_info` works, `update_employee` doesn't

## Root Cause
The function was likely designed for a workflow-based update system where changes go through approval. However, the approval workflow was never implemented, leaving this function as essentially a no-op that pretends to work.

## How to Fix

### Code Changes
Either implement the workflow or apply changes directly:

```python
# ✅ FIXED - Option 1: Apply changes directly (like update_contact_info)
async def update_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # ... validation ...

    changes = []
    for key, value in updates.items():
        if hasattr(employee, key):
            old_val = getattr(employee, key)
            setattr(employee, key, value)  # Actually apply the change
            changes.append({
                "field": key,
                "old_value": str(old_val),
                "new_value": str(value)
            })

    return {
        "employee_id": employee_id,
        "status": "APPLIED",  # Reflect actual status
        "changes": changes,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }

# ✅ FIXED - Option 2: Implement proper workflow
async def update_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
    # ... validation ...

    # Create pending change request
    change_request_id = f"CHG-{uuid.uuid4().hex[:8]}"
    self.simulator.pending_changes[change_request_id] = {
        "employee_id": employee_id,
        "updates": updates,
        "requested_by": principal_id,
        "status": "PENDING_APPROVAL"
    }

    return {
        "change_request_id": change_request_id,
        "status": "PENDING_APPROVAL",
        # ...
    }
```

### Steps
1. Decide on the intended behavior (direct update vs workflow)
2. If direct: Add `setattr()` calls to apply changes
3. If workflow: Implement `pending_changes` storage and approval endpoints
4. Update tests to verify changes are actually persisted
5. Update documentation to clarify the behavior

## Verification

### Test Cases
1. Call `update_employee` with valid updates
2. Call `get_employee` for the same employee
3. Verify the updates are reflected in the response

### Verification Steps
1. Write integration test for update-then-read flow
2. Verify in-memory state is updated
3. Test with multiple field updates

## Related Issues
- Contrast with `update_contact_info` which does apply changes

---
*Discovered: 2026-02-03*
