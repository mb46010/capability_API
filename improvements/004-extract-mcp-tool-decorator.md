# 004: Extract MCP Tool Boilerplate into Decorator

## Impact
**Effort**: Low (2-3 hours) | **Impact**: Medium | **Priority**: 2

## Location
- **File(s)**: `src/mcp/tools/hcm.py`, `src/mcp/tools/time.py`, `src/mcp/tools/payroll.py`
- **Component/Module**: MCP Tools Layer

## Current State

Every MCP tool function repeats the same boilerplate pattern:

```python
async def get_employee(ctx: Any, employee_id: str) -> str:
    user_token, principal, error = await authenticate_and_authorize(ctx, "get_employee")
    if error: return f"ERROR: {error}"

    principal_id = principal.subject

    try:
        mcp_token = await get_mcp_token(user_token)
        coro = backend_client.call_action(...)
        response = await coro
        audit_logger.log("get_employee", {...}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        error_msg = map_backend_error(e)
        audit_logger.log("get_employee", {...}, principal_id, status="error")
        return f"ERROR: {error_msg}"
```

This pattern is repeated ~15 times across 3 files with only domain/action/parameters changing.

## Proposed Improvement

Create a decorator that handles authentication, token exchange, error mapping, and audit logging, reducing each tool to its essential logic.

## Benefits

- **Maintainability**: Single place to update auth/logging logic
- **Readability**: Tool functions focus on their unique parameters
- **Consistency**: Impossible to forget auth check or audit log
- **Developer Productivity**: Adding new tools is trivial

**Lines of code reduced**: ~300 lines -> ~100 lines (66% reduction)

## Implementation

### Approach
Create a `@mcp_tool` decorator that wraps functions with standard boilerplate.

### Estimated Effort
2-3 hours

### Steps
1. Create decorator in `src/mcp/lib/decorators.py`
2. Refactor one tool (e.g., `get_employee`) as proof of concept
3. Migrate remaining tools
4. Update tests

## Example

### Before
```python
# src/mcp/tools/hcm.py - repeated 5 times
async def get_employee(ctx: Any, employee_id: str) -> str:
    user_token, principal, error = await authenticate_and_authorize(ctx, "get_employee")
    if error: return f"ERROR: {error}"
    principal_id = principal.subject
    try:
        mcp_token = await get_mcp_token(user_token)
        coro = backend_client.call_action(
            domain="workday.hcm",
            action="get_employee",
            parameters={"employee_id": employee_id},
            token=mcp_token
        )
        response = await coro
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id)
        return str(response.get("data", {}))
    except Exception as e:
        error_msg = map_backend_error(e)
        audit_logger.log("get_employee", {"employee_id": employee_id}, principal_id, status="error")
        return f"ERROR: {error_msg}"

async def get_manager_chain(ctx: Any, employee_id: str) -> str:
    # Same boilerplate, different action name...
```

### After
```python
# src/mcp/lib/decorators.py
from functools import wraps

def mcp_tool(domain: str, action: str):
    """Decorator that handles MCP tool boilerplate."""
    def decorator(func):
        @wraps(func)
        async def wrapper(ctx, *args, **kwargs):
            # 1. Auth
            user_token, principal, error = await authenticate_and_authorize(ctx, action)
            if error:
                return f"ERROR: {error}"

            principal_id = principal.subject
            parameters = func(*args, **kwargs)  # Tool returns just parameters

            try:
                # 2. Token exchange
                mcp_token = await get_mcp_token(user_token)

                # 3. Backend call
                response = await backend_client.call_action(
                    domain=domain,
                    action=action,
                    parameters=parameters,
                    token=mcp_token
                )

                # 4. Audit
                audit_logger.log(action, parameters, principal_id)
                return str(response.get("data", {}))

            except Exception as e:
                audit_logger.log(action, parameters, principal_id, status="error")
                return f"ERROR: {map_backend_error(e)}"

        return wrapper
    return decorator
```

```python
# src/mcp/tools/hcm.py - clean and focused
from src.mcp.lib.decorators import mcp_tool

@mcp_tool(domain="workday.hcm", action="get_employee")
def get_employee(employee_id: str) -> dict:
    """Look up employee profile."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.hcm", action="get_manager_chain")
def get_manager_chain(employee_id: str) -> dict:
    """Get reporting line."""
    return {"employee_id": employee_id}

@mcp_tool(domain="workday.hcm", action="get_org_chart")
def get_org_chart(root_id: str, depth: int = 2) -> dict:
    """View org structure."""
    return {"root_id": root_id, "depth": depth}
```

## Considerations

- Context (`ctx`) still needed for auth extraction - pass through decorator
- Some tools may need custom response formatting - allow override
- Maintain backward compatibility during migration
- Ensure proper async handling in decorator

## Related Improvements
- None

---
*Identified: 2026-02-01*
