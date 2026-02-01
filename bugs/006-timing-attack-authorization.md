# BUG-006: Timing Attack Vulnerability in Authorization Checks

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `src/adapters/workday/services/hcm.py`, `src/adapters/workday/services/time.py`, `src/adapters/workday/services/payroll.py`
- **Line(s)**: Various authorization check sequences

## Issue Description
Authorization checks are performed AFTER existence checks, creating timing differences that allow attackers to enumerate valid employee IDs:

```python
# ❌ VULNERABLE: Existence check before authorization
async def get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = params.get("employee_id")
    principal_id = params.get("principal_id")

    # Existence check happens FIRST
    employee = self.simulator.employees.get(employee_id)
    if not employee:
        raise EmployeeNotFoundError(employee_id)  # Different timing/response

    # Authorization check happens AFTER
    if principal_type == "HUMAN" and principal_id != employee_id:
        # Only reach here if employee EXISTS
        raise WorkdayError("...", "UNAUTHORIZED")
```

An attacker can distinguish between:
1. Employee doesn't exist (fast response, 404)
2. Employee exists but no access (slower response, 403)

## Impact
- **User Enumeration**: Attackers can build a list of valid employee IDs by measuring response times or status codes
- **Targeted Attacks**: Once valid IDs are known, attackers can focus social engineering or other attacks
- **Privacy Violation**: Organization structure can be partially mapped

## Root Cause
The code follows a natural programming pattern (check existence, then permissions) but this order leaks information. Authorization should be checked before revealing whether a resource exists.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Authorization before existence check
async def get_employee(self, params: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = params.get("employee_id")
    principal_id = params.get("principal_id")
    principal_type = params.get("principal_type", "HUMAN")

    # Authorization check FIRST (before revealing existence)
    if principal_type == "HUMAN" and principal_id and principal_id != employee_id:
        raise WorkdayError("Access denied", "UNAUTHORIZED")

    # Now check existence (attacker already knows they have permission if they get here)
    employee = self.simulator.employees.get(employee_id)
    if not employee:
        raise WorkdayError("Access denied", "UNAUTHORIZED")  # Same error as above!

    # ... rest of function
```

**For cases where we can't check auth before existence (e.g., manager relationship):**

```python
# ✅ FIXED: Return same response regardless of reason
async def approve(self, params: Dict[str, Any]) -> Dict[str, Any]:
    request_id = params.get("request_id")
    principal_id = params.get("principal_id")

    request = self.simulator.requests.get(request_id)

    # Check all conditions, return generic error
    # Don't reveal whether request exists, employee exists, or relationship exists
    if not request:
        raise WorkdayError("Access denied", "UNAUTHORIZED")

    employee = self.simulator.employees.get(request.employee_id)
    if not employee:
        raise WorkdayError("Access denied", "UNAUTHORIZED")

    if principal_type == "HUMAN" and principal_id:
        if not employee.manager or employee.manager.employee_id != principal_id:
            raise WorkdayError("Access denied", "UNAUTHORIZED")

    # ... rest of function
```

### Steps
1. Audit all service methods for check ordering
2. Restructure to check authorization before revealing existence where possible
3. Where not possible, ensure same error response for all failure cases
4. Add constant-time comparison for sensitive string comparisons (if applicable)

## Verification

### Test Cases
1. Time requests for non-existent vs existing employees - should have similar response times
2. Compare response codes for different failure scenarios - should be identical
3. Verify legitimate users can still access their data normally

### Verification Steps
```bash
# Timing test (simplified - use proper tools for real testing)
time curl -s -X POST http://localhost:8000/actions/workday/get_employee \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"parameters": {"employee_id": "NONEXISTENT"}}'

time curl -s -X POST http://localhost:8000/actions/workday/get_employee \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"parameters": {"employee_id": "EMP-001"}}'

# Response codes should be the same (403 or 401)
# Timing should be similar
```

## Related Issues
- Related to BUG-005 (sensitive data in error messages)

---
*Discovered: 2026-02-01*
