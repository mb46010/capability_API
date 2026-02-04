# Bug Report: HR MCP Server Implementation Gaps

**Date**: 2026-02-04
**Status**: Open
**Priority**: High

## Overview
A review of the `src/mcp` implementation against `specs/005-hr-mcp-server/spec.md` and `specs/006-mcp-token-exchange/spec.md` revealed several discrepancies, ranging from security risks (exception leaks, race conditions) to functional gaps (audit logging, idempotency).

## Issues

### 1. Inconsistent Principal Type for MFA Bypass (Potential Blocker)
- **Location**: `src/mcp/lib/decorators.py` vs `src/mcp/adapters/auth.py`
- **Spec Reference**: `005-hr-mcp-server` FR-004 (AI Agent role), MFA Clarifications.
- **Description**:
  - `src/mcp/adapters/auth.py` (and `discovery.py`) identifies the agent role as `"AI_AGENT"`.
  - `src/mcp/lib/decorators.py` checks for `principal.principal_type != "MACHINE"` to bypass MFA checks.
- **Impact**: Since `"AI_AGENT" != "MACHINE"`, the bypass logic fails. If an AI Agent attempts to use a tool that requires MFA (or if the default policy changes), it will receive an `MFA_REQUIRED` error instead of being allowed (or the check is effectively dead code). The terminology must be consistent (prefer `"AI_AGENT"` as per Spec FR-004).

### 2. Unsafe Exception Handling (Information Leak)
- **Location**: `src/mcp/lib/errors.py`
- **Spec Reference**: `005-hr-mcp-server` Edge Cases ("Sanitize and Return Generic Error").
- **Description**: The `map_backend_error` function handles HTTP errors correctly but has a catch-all for other exceptions:
  ```python
  logger.error(f"Unhandled error: {str(e)}")
  return f"INTERNAL_ERROR: {str(e)}"
  ```
- **Impact**: This leaks raw exception details (e.g., stack trace fragments, internal variable values) to the client/LLM, violating the security requirement to sanitize internal errors.

### 3. Token Cache TTL Race Condition
- **Location**: `src/mcp/adapters/auth.py`
- **Spec Reference**: `006-mcp-token-exchange` FR-008 ("Cache valid exchanged tokens (e.g., for 4 minutes)").
- **Description**: The code sets the cache TTL to 300 seconds (5 minutes):
  ```python
  _mcp_token_cache: TTLCache = TTLCache(maxsize=5000, ttl=300)
  ```
  The exchanged token likely has a TTL of exactly 5 minutes.
- **Impact**: Caching for the full duration creates a race condition where the token expires *exactly* when it is retrieved from the cache, causing the subsequent backend call to fail with 401. The cache TTL should be padded (e.g., 240 seconds) to ensure the token is still valid when used.

### 4. Incomplete Audit Logging (Missing Response Payloads)
- **Location**: `src/mcp/lib/decorators.py`
- **Spec Reference**: `005-hr-mcp-server` FR-010 ("Capture full request/response payloads... for write actions").
- **Description**: The decorator currently logs `parameters` (request) for *all* tools but does **not** log the `response` data for any tool.
  ```python
  # 6. Audit Success
  audit_logger.log(effective_tool_name, parameters, principal_id)
  return str(response.get("data", {}))
  ```
- **Impact**: High-risk write actions (e.g., `request_time_off`) do not have their outcomes recorded in the audit log, making it impossible to verify what was returned to the agent.

### 5. Inconsistent Idempotency Implementation
- **Location**: `src/mcp/tools/hcm.py` (`update_contact_info`)
- **Spec Reference**: `005-hr-mcp-server` Idempotency Strategy ("Write actions... will utilize unique transaction IDs").
- **Description**: `request_time_off` in `time.py` correctly generates a `transaction_id`. However, `update_contact_info` in `hcm.py` (also a write action) does not generate or accept a transaction ID.
- **Impact**: The contact update operation lacks the idempotency controls promised in the architecture, potentially leading to issues on retry.

### 6. Documentation/Implementation Mismatch (`list_pay_statements`)
- **Location**: `specs/005-hr-mcp-server/spec.md` vs `src/mcp/tools/payroll.py`
- **Spec Reference**: FR-003.
- **Description**: FR-003 lists only `get_compensation` and `get_pay_statement`. The code (and `api_reference.md`) includes `list_pay_statements`.
- **Impact**: Minor documentation inconsistency. The spec should be updated to reflect the implemented tool.
