# BUG-002: Guest Authentication Enabled in Production Configuration

## Severity
🔴 CRITICAL

## Location
- **File(s)**: `hr-nexus/app-config.yaml`, `hr-nexus/app-config.production.yaml`
- **Line(s)**: app-config.yaml:66-70, app-config.production.yaml:31-33

## Issue Description
Both development and production Backstage configurations have guest authentication enabled. Guest authentication allows unauthenticated users to access the system with limited identity information.

```yaml
# ❌ VULNERABLE - Guest auth in production
auth:
  providers:
    guest: {}
```

Combined with the allow-all permission policy (BUG-001), this creates a scenario where completely unauthenticated users can access and potentially modify the HR capability catalog.

## Impact
- **Public exposure**: HR capability catalog visible without authentication
- **Anonymous modifications**: Combined with BUG-001, anonymous users can modify entities
- **Audit trail bypass**: Guest users have minimal identity info for audit purposes
- **Compliance violation**: Violates principle of authenticated access for sensitive HR data

## Root Cause
The production configuration file (`app-config.production.yaml`) was scaffolded from the development template and guest authentication was not disabled. The guest provider is intended solely for local development and testing.

## How to Fix

### Code Changes
Remove guest authentication from production configuration:

```yaml
# ✅ FIXED - Proper auth for production
auth:
  providers:
    # Remove guest: {} entirely

    # Configure proper identity provider
    okta:
      development:
        clientId: ${OKTA_CLIENT_ID}
        clientSecret: ${OKTA_CLIENT_SECRET}
        audience: ${OKTA_AUDIENCE}
```

### Steps
1. Edit `hr-nexus/app-config.production.yaml`
2. Remove the `guest: {}` line from `auth.providers`
3. Configure a proper identity provider (Okta, Azure AD, etc.)
4. Update Backstage backend to use the appropriate auth module
5. Ensure proper redirect URIs are configured

## Verification

### Test Cases
1. Access Backstage production URL without authentication - should redirect to login
2. Attempt API calls without Bearer token - should receive 401
3. Verify authenticated users can access appropriate resources

### Verification Steps
1. Deploy configuration change to staging
2. Verify guest access is denied
3. Verify proper auth flow works end-to-end

## Related Issues
- [BUG-001](001-backstage-allow-all-permission-policy.md) - Allow-all permission policy

---
*Discovered: 2026-02-03*
