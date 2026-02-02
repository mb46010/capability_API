# BUG-011: Circular Reference Handling Causes Stack Overflow Risk

## Severity
🟢 LOW

## Location
- **File(s)**: `src/adapters/workday/services/hcm.py`
- **Line(s)**: 96-140 (get_manager_chain), 52-94 (get_org_chart)

## Issue Description
While `get_manager_chain` has circular reference detection, `get_org_chart` does not. A malicious or corrupted fixture with circular manager references could cause infinite recursion in `get_org_chart`:

```python
# get_manager_chain has protection (good):
async def get_manager_chain(self, params: Dict[str, Any]) -> Dict[str, Any]:
    visited = {employee_id}
    while current_emp.manager:
        mgr_id = current_emp.manager.employee_id
        if mgr_id in visited:
            raise WorkdayError(f"Circular manager reference detected: ...", "DATA_INTEGRITY_ERROR")
        visited.add(mgr_id)
        # ...

# get_org_chart has NO protection (vulnerable):
async def get_org_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
    async def build_node(emp_id, current_depth):
        if current_depth > depth:
            return None

        # No circular reference check!
        for report in self.simulator.employees.values():
            if report.manager and report.manager.employee_id == emp_id:
                child = await build_node(report.employee_id, current_depth + 1)
```

Note: The `depth` parameter does provide some protection, but:
1. An attacker could set a very high depth
2. The recursion happens per-branch, so a wide tree with high depth could still exhaust the stack

## Impact
- **Denial of Service**: Crafted fixtures with cycles could crash the server
- **Resource Exhaustion**: Deep/wide recursion consumes memory and CPU
- **Limited Scope**: Requires ability to modify fixtures (admin or file system access)

## Root Cause
`get_org_chart` uses depth limiting but not explicit cycle detection. The fixture validation checks for circular manager references but only in the upward direction.

## How to Fix

### Code Changes

```python
# ✅ FIXED: Add cycle detection and depth limits
async def get_org_chart(self, params: Dict[str, Any]) -> Dict[str, Any]:
    root_id = params.get("root_id")
    depth = min(params.get("depth", 2), 10)  # Cap maximum depth

    if not root_id:
        raise WorkdayError("Missing root_id", "INVALID_PARAMS")

    if root_id not in self.simulator.employees:
        raise EmployeeNotFoundError(root_id)

    visited = set()  # Track visited nodes

    async def build_node(emp_id, current_depth):
        if current_depth > depth:
            return None
        if emp_id in visited:
            # Circular reference - skip this branch
            return None

        visited.add(emp_id)

        emp = self.simulator.employees.get(emp_id)
        if not emp:
            return None

        node = {
            "employee_id": emp.employee_id,
            "name": get_display_name(emp),
            "title": emp.job["title"] if isinstance(emp.job, dict) else (emp.job.title if hasattr(emp.job, "title") else "Unknown"),
            "reports": []
        }

        if current_depth < depth:
            for report in self.simulator.employees.values():
                if report.manager and report.manager.employee_id == emp_id:
                    child = await build_node(report.employee_id, current_depth + 1)
                    if child:
                        node["reports"].append(child)

        return node

    # ... rest of function
```

### Steps
1. Add maximum depth cap (e.g., 10) regardless of user input
2. Add visited set to detect cycles
3. Consider converting to iterative approach for very large orgs

## Verification

### Test Cases
1. Normal org chart request - should work as before
2. Request with depth > max - should be capped
3. Fixture with circular reference - should handle gracefully without crash
4. Large org with many levels - should complete without stack overflow

### Verification Steps
```python
# Test circular reference handling
def test_org_chart_circular_reference():
    # Create circular reference in fixtures
    emp1 = simulator.employees["EMP-001"]
    emp2 = simulator.employees["EMP-002"]
    emp1.manager = ManagerRef(employee_id="EMP-002", display_name="...")
    emp2.manager = ManagerRef(employee_id="EMP-001", display_name="...")

    # Should not crash
    result = await service.get_org_chart({"root_id": "EMP-001", "depth": 5})
    # Result should be limited, not infinite
```

## Related Issues
- None

---
*Discovered: 2026-02-01*
