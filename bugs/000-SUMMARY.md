# Bug Review Summary

**Review Date**: 2026-02-01
**Codebase**: capability_API (HR AI Platform Capability API)
**Files Reviewed**: 45+ Python source files

## Overview

This review analyzed the Capability API codebase, a FastAPI-based service that provides governed access to HR operations (Workday simulator) with OIDC authentication, policy-based authorization, and audit logging. The system follows hexagonal architecture with a mock Okta provider for local development.

## Statistics

- **Total Issues Found**: 12
- **Critical**: 2
- **High**: 2
- **Medium**: 4
- **Low**: 4

# Done


## Critical Issues (Immediate Action Required)

| # | Issue | File | Impact |
|---|-------|------|--------|
| [001](001-demo-reset-no-auth.md) | Demo Reset Endpoint Missing Authentication | `src/api/routes/demo.py` | Any unauthenticated user can reset all service caches, causing DoS and potential security bypass |
| [002](002-test-reload-no-auth.md) | Test Reload Fixtures Missing Authentication | `src/api/routes/actions.py` | Any unauthenticated user can reload fixtures, potentially loading malicious data |

## High Priority Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| [003](003-mock-okta-test-endpoints-exposed.md) | Mock Okta Test Endpoints Exposed | `src/adapters/auth/mock_okta.py` | Anyone can create admin tokens or arbitrary users via /test/* endpoints |
| [004](004-mcp-token-verification-disabled.md) | MCP Token Verification Disabled | `src/mcp/adapters/auth.py` | Token signature not verified, allowing forged tokens to pass RBAC checks |
| [005](005-sensitive-data-in-exception-messages.md) | Sensitive Data in Exception Messages | Workday services | Error messages leak principal IDs and relationships |
| [006](006-timing-attack-authorization.md) | Timing Attack in Authorization | Workday services | Different response times reveal resource existence |
| [007](007-idempotency-cache-unbounded.md) | Unbounded Idempotency Cache | `src/adapters/workday/client.py` | Memory grows indefinitely, potential OOM |
| [008](008-mcp-token-cache-memory-leak.md) | MCP Token Cache Memory Leak | `src/mcp/adapters/auth.py` | Token cache never cleaned, memory growth |


# To Do

## Medium Priority Issues

(None)

## Low Priority Issues

| # | Issue | File | Impact |
|---|-------|------|--------|
| [009](009-flow-status-idor.md) | Flow Status Information Disclosure | `src/domain/services/flow_service.py` | Different errors for not-found vs unauthorized |
| [010](010-uvicorn-reload-production.md) | Uvicorn Reload in Production | `src/main.py` | Reload mode always enabled, performance overhead |
| [011](011-circular-reference-dos.md) | Circular Reference Stack Overflow | `src/adapters/workday/services/hcm.py` | Org chart missing cycle detection |
| [012](012-audit-log-path-traversal.md) | Audit Log Path Traversal Risk | `src/adapters/filesystem/logger.py` | Path not validated (currently hardcoded but future risk) |

## Recommendations

### Immediate Actions (This Sprint)

1. **Add authentication to admin endpoints** (BUG-001, BUG-002)
   - These are critical and straightforward to fix
   - Add `get_current_principal` dependency and admin group check
   - Gate by environment where appropriate

2. **Protect Mock Okta test endpoints** (BUG-003)
   - Either require a secret key or remove from HTTP surface
   - Tests can use the provider directly

3. **Enable token verification in MCP layer** (BUG-004)
   - Verify JWT signature before making authorization decisions
   - Or remove RBAC from MCP layer entirely

### Short-Term (Next 2 Sprints)

4. **Standardize error responses** (BUG-005, BUG-006, BUG-009)
   - Return generic "Access denied" for all authorization failures
   - Check authorization before existence where possible
   - Log detailed errors server-side only

5. **Add cache eviction** (BUG-007, BUG-008)
   - Implement TTL and max size for both caches
   - Consider using `cachetools.TTLCache`

### Longer-Term

6. **Security hardening** (BUG-010, BUG-011, BUG-012)
   - Environment-aware uvicorn configuration
   - Add cycle detection to org chart
   - Validate log paths defensively

## Review Coverage

**Reviewed**:
- [x] Source code (`src/`)
  - [x] API layer (`src/api/`)
  - [x] Domain services (`src/domain/services/`)
  - [x] Adapters (`src/adapters/`)
  - [x] MCP server (`src/mcp/`)
- [x] Configuration files
- [x] Policy definitions

**Not Reviewed**:
- [ ] Third-party dependencies (recommend `pip audit` or `safety check`)
- [ ] Infrastructure/deployment configuration
- [ ] Frontend code (if any)
- [ ] Integration with real Okta (production configuration)

## Positive Observations

The codebase demonstrates several security best practices:

1. **Defense in depth**: Multiple layers of authorization (policy engine + connector-level checks)
2. **Audit logging**: Comprehensive logging with PII redaction
3. **Security headers**: Proper headers in responses (X-Content-Type-Options, etc.)
4. **Token provenance**: Good tracking of token exchange chains
5. **Error sanitization**: Production environment sanitizes error messages for 5xx errors
6. **Policy-based access control**: Declarative, auditable policy definitions
7. **MFA enforcement**: Sensitive operations require MFA verification

---

*Generated by Code Bug Finder - 2026-02-01*
