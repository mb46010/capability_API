# AI Reference: HR Platform MCP Server

This document provides a high-density technical reference for AI agents working on the HR MCP Server module.

## 🎯 Purpose
The MCP Server acts as a secure, role-governed gateway between AI models (clients) and the Capability API (backend). It enforces RBAC, handles MFA requirements, and ensures PII redaction in logs.

## 🛠 Tech Stack
- **Framework**: FastMCP 3.0 (Python-native)
- **Communication**: HTTP/1.1 (JSON) to Backend
- **Auth**: Bearer Token Passthrough (OIDC)
- **Validation**: Pydantic V2

## 🧩 Core Concepts

### 1. Identity & RBAC
- **Token Source**: Extracted from MCP transport context/metadata (`X-Request-ID` and `Authorization`).
- **Principal Types**: `AI_AGENT`, `EMPLOYEE`, `ADMIN`.
- **RBAC Logic**: Handled in `src/mcp/adapters/auth.py`. Access is denied at the MCP layer if the principal type lacks the required capability.

### 2. Multi-Factor Authentication (MFA)
- **Requirement**: Mandatory for all `workday.payroll.*` tools.
- **Enforcement**: Checks for `amr: ["mfa"]` in the OIDC token. `MACHINE` types can bypass if authorized by backend policy.

### 3. PII Redaction (Article VIII)
- **Implementation**: `src/mcp/lib/logging.py` contains a `PIIMaskingFilter`.
- **Scope**: Masks emails, phones, SSNs, and salary data in both standard logs and the JSONL audit trail.

### 4. Idempotency
- **Write Actions**: Automatically generate a `TXN-` prefixed UUID if the client does not provide a transaction ID.
- **Scoping**: The backend scopes idempotency keys to the principal and action, ensuring that unique transactions are handled correctly even if keys are reused across different contexts.
- **Consistency**: Relies on backend optimistic concurrency and the simulator's internal cache.

## 📂 File Structure
- `server.py`: FastMCP entry point and tool registration.
- `tools/`: Domain logic (hcm, time, payroll).
- `adapters/`: External interfaces (Capability API client, Auth extractor).
- `models/`: Pydantic schemas for tool inputs/outputs.
- `lib/`: Utilities (PII-masking logging, configuration, error mapping).

## ⚠️ Critical Rules for AI Agents
1. **Never Bypass Auth**: Every tool MUST call `authenticate_and_authorize(ctx, tool_name)`.
2. **Mask PII**: Use the `audit_logger` for any capability invocation. Never use `print()`.
3. **Await Backend**: All calls to `backend_client.call_action` MUST be awaited.
4. **Sanitize Errors**: Map 5xx errors to generic messages using `map_backend_error`.
5. **No God Files**: Keep `server.py` thin; implement tool logic in `src/mcp/tools/`.
