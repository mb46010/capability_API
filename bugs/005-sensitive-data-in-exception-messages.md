# BUG-005: Sensitive Information in Exception Messages

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/services/hcm.py`, `src/adapters/workday/services/time.py`, `src/adapters/workday/services/payroll.py`
- **Line(s)**: Multiple

## Issue Description
Several exception messages include user-controlled input and internal identifiers that could leak sensitive information to attackers:

```python
# ❌ VULNERABLE: Leaks principal/employee IDs in error messages
raise WorkdayError(f"Principal {principal_id} cannot update data for {employee_id}", "UNAUTHORIZED")
raise WorkdayError(f"Principal {principal_id} is not the manager of {request.employee_id}", "UNAUTHORIZED")
raise WorkdayError(f"Principal {principal_id} cannot access data for {employee_id}", "UNAUTHORIZED")
```

These messages are returned to clients in API responses and can reveal:
1. Whether a specific employee ID exists (enumeration)
2. The relationship between principals and employees
3. Manager-report relationships

## Impact
- **Information Disclosure**: Error messages reveal internal user identifiers and organizational relationships
- **User Enumeration**: Attackers can probe for valid employee IDs by analyzing error messages
- **Relationship Discovery**: Error messages reveal manager-employee relationships
- **IDOR Detection**: Different error messages for "not authorized" vs "not found" allow attackers to map access permissions

## Root Cause
Error messages were designed for debugging convenience rather than security. The same error message should be returned regardless of whether:
- The target doesn't exist
- The principal lacks permission
- The relationship is invalid

## How to Fix

### Code Changes

```python
# ✅ FIXED: Generic error messages that don't leak information
# hcm.py, time.py, payroll.py

# Before:
raise WorkdayError(f"Principal {principal_id} cannot update data for {employee_id}", "UNAUTHORIZED")

# After:
raise WorkdayError("Access denied", "UNAUTHORIZED")

# Before:
raise WorkdayError(f"Principal {principal_id} is not the manager of {request.employee_id}", "UNAUTHORIZED")

# After:
raise WorkdayError("Access denied", "UNAUTHORIZED")

# Before:
if employee_id not in self.simulator.employees:
    raise EmployeeNotFoundError(employee_id)
# ...
if principal_type == "HUMAN" and principal_id != employee_id:
    raise WorkdayError(f"Principal {principal_id} cannot access data for {employee_id}", "UNAUTHORIZED")

# After: Check authorization BEFORE existence for timing-safe comparison
if principal_type == "HUMAN" and principal_id != employee_id:
    raise WorkdayError("Access denied", "UNAUTHORIZED")
if employee_id not in self.simulator.employees:
    raise WorkdayError("Access denied", "UNAUTHORIZED")  # Same message!
```

### Steps
1. Identify all error messages that include user-controlled data
2. Replace with generic "Access denied" or similar message
3. Log detailed information server-side for debugging (already done via audit logger)
4. Consider ordering checks to prevent timing attacks (auth before existence checks)

## Verification

### Test Cases
1. Request data for non-existent employee - should return "Access denied"
2. Request data for existing employee without permission - should return "Access denied" (same message)
3. Request data for own employee - should succeed
4. Verify audit logs still contain detailed information for debugging

### Verification Steps
```bash
# Test with non-existent employee
curl -X POST http://localhost:8000/actions/workday/get_employee \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"parameters": {"employee_id": "EMP-NONEXISTENT"}}'
# Should return generic "Access denied"

# Test with existing employee, no permission
curl -X POST http://localhost:8000/actions/workday/get_employee \
  -H "Authorization: Bearer $USER_TOKEN" \
  -d '{"parameters": {"employee_id": "EMP-SOMEONE-ELSE"}}'
# Should return same "Access denied" message

# Verify detailed errors are in audit log
tail -1 logs/audit.jsonl | jq
```

## Related Issues
- Related to BUG-006 (timing attacks)

---
*Discovered: 2026-02-01*
