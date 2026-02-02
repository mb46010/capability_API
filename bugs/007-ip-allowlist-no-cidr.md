# BUG-007: IP Allowlist Does Not Support CIDR/Ranges Despite Schema Intent

## Severity
🟡 MEDIUM

## Location
- **File(s)**: src/domain/entities/policy.py, src/domain/services/policy_engine.py
- **Line(s)**: src/domain/entities/policy.py:34-38, src/domain/services/policy_engine.py:200-205

## Issue Description
The policy schema describes `ip_allowlist` as "Allowed source IP addresses or ranges," but the enforcement logic only checks for exact string matches. CIDR ranges (e.g., `10.0.0.0/24`) or IP ranges will never match, leading to false denials even when the policy appears to allow access.

**Current behavior:**
```python
# ❌ VULNERABLE
if request_ip not in rule.conditions.ip_allowlist:
    return False
```

## Impact
- Policies that specify CIDR ranges will silently deny valid requests.
- Causes unexpected access failures in production when IP ranges are used.

## Root Cause
The evaluation code does not parse or match CIDR/range values; it only compares strings.

## How to Fix

### Code Changes
Parse allowlist entries with `ipaddress` and support exact IPs plus CIDR ranges.

```python
# ✅ FIXED (example)
import ipaddress

ip = ipaddress.ip_address(request_ip)
allowed = False
for entry in rule.conditions.ip_allowlist:
    if "/" in entry:
        if ip in ipaddress.ip_network(entry, strict=False):
            allowed = True
            break
    elif request_ip == entry:
        allowed = True
        break

if not allowed:
    return False
```

### Steps
1. Add `ipaddress`-based matching in `_evaluate_conditions`.
2. Add tests for exact IPs and CIDR ranges.
3. Update documentation to clarify supported formats.

## Verification

### Test Cases
- Allowlist with exact IP permits that IP.
- Allowlist with CIDR permits IPs inside the subnet and denies those outside.

### Verification Steps
1. Add a policy with `ip_allowlist: ["10.0.0.0/24"]`.
2. Evaluate a request from `10.0.0.5` and confirm it is allowed.
3. Evaluate a request from `10.0.1.5` and confirm it is denied.

## Related Issues
- None.

---
*Discovered: 2026-02-02T22:06:45Z*
