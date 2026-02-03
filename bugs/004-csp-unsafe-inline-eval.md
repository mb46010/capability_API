# BUG-004: Weak Content Security Policy with unsafe-inline and unsafe-eval

## Severity
🟠 HIGH

## Location
- **File(s)**: `hr-nexus/app-config.yaml`
- **Line(s)**: 21-22

## Issue Description
The Backstage backend CSP configuration allows `'unsafe-inline'` and `'unsafe-eval'` for script sources:

```yaml
# ❌ VULNERABLE - Weak CSP
csp:
  connect-src: ["'self'", 'http:', 'https:']
  script-src: ["'self'", "'unsafe-inline'", "'unsafe-eval'", 'https://unpkg.com']
```

These directives significantly weaken the Content Security Policy:
- `'unsafe-inline'`: Allows inline `<script>` tags and event handlers, enabling XSS attacks
- `'unsafe-eval'`: Allows `eval()` and similar dynamic code execution, enabling code injection
- `https://unpkg.com`: Allows loading any package from unpkg, potential supply chain risk

## Impact
- **XSS vulnerability**: Attackers can inject and execute malicious scripts
- **Code injection**: Dynamic code execution enables sophisticated attacks
- **Supply chain risk**: Any malicious package on unpkg can be loaded
- **Session hijacking**: XSS can steal tokens and session data

## Root Cause
This is the default Backstage CSP configuration designed for maximum compatibility. It should be tightened for production deployments, especially when handling sensitive HR data.

## How to Fix

### Code Changes
Implement a stricter CSP policy:

```yaml
# ✅ FIXED - Strict CSP for production
csp:
  default-src: ["'self'"]
  connect-src: ["'self'", "https://api.yourbackend.com"]
  script-src:
    - "'self'"
    - "'sha256-<hash-of-inline-scripts>'"  # Use hashes instead of unsafe-inline
  style-src: ["'self'", "'unsafe-inline'"]  # Often needed for styling
  img-src: ["'self'", "data:", "https:"]
  font-src: ["'self'"]
  frame-ancestors: ["'none'"]
  base-uri: ["'self'"]
  form-action: ["'self'"]
```

### Steps
1. Audit all inline scripts in Backstage and compute their SHA-256 hashes
2. Replace `'unsafe-inline'` with specific script hashes
3. Remove `'unsafe-eval'` - refactor any code using `eval()`
4. Replace `https://unpkg.com` with specific versioned URLs or host packages locally
5. Add `frame-ancestors: ["'none'"]` to prevent clickjacking
6. Test thoroughly as strict CSP may break functionality

## Verification

### Test Cases
1. Attempt to inject inline script via XSS vector - should be blocked
2. Verify legitimate Backstage functionality still works
3. Check browser console for CSP violation reports

### Verification Steps
1. Deploy updated CSP to staging
2. Run full Backstage E2E test suite
3. Perform manual XSS testing
4. Monitor CSP violation reports

## Related Issues
- [BUG-001](001-backstage-allow-all-permission-policy.md) - Combined with allow-all policy increases risk

---
*Discovered: 2026-02-03*
