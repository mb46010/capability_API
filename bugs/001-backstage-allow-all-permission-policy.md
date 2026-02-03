# BUG-001: Backstage Allow-All Permission Policy in Production Configuration

## Severity
🔴 CRITICAL

## Location
- **File(s)**: `hr-nexus/packages/backend/src/index.ts`
- **Line(s)**: 44-46

## Issue Description
The Backstage backend is configured with `@backstage/plugin-permission-backend-module-allow-all-policy`, which grants unrestricted access to all users and bypasses all permission checks. This is explicitly intended for development only, but the production configuration (`app-config.production.yaml`) does not override this setting.

```typescript
// ❌ VULNERABLE - Allow-all policy in production
backend.add(
  import('@backstage/plugin-permission-backend-module-allow-all-policy'),
);
```

When deployed to production, any authenticated user (even guests) can:
- Modify catalog entities
- Access scaffolder templates
- View sensitive TechDocs
- Perform administrative operations

## Impact
- **Unauthorized access**: Any user can perform any action in Backstage
- **Data exposure**: Sensitive HR capability catalog data exposed to all users
- **Compliance violation**: RBAC requirements are completely bypassed
- **Audit failure**: Actions cannot be attributed to appropriate permission levels

## Root Cause
The Backstage backend uses a development-friendly default configuration that was not properly hardened for production deployment. The permission policy module should be swapped for a proper RBAC implementation before production use.

## How to Fix

### Code Changes
Replace the allow-all policy with a proper permission policy:

```typescript
// ✅ FIXED - Use a proper permission policy
// Option 1: Create a custom policy
backend.add(import('./plugins/permission'));

// Option 2: Use built-in deny-all and whitelist
// backend.add(import('@backstage/plugin-permission-backend-module-deny-all-policy'));
```

### Steps
1. Create a custom permission policy module at `hr-nexus/packages/backend/src/plugins/permission.ts`
2. Define permission rules that align with the HR platform's RBAC requirements
3. Remove the allow-all policy import
4. Add the custom permission policy
5. Test that unauthorized users cannot perform privileged operations

## Verification

### Test Cases
1. Authenticate as a non-admin user and attempt to modify catalog entities - should fail
2. Attempt to access scaffolder admin endpoints - should fail
3. Verify admin users retain appropriate access

### Verification Steps
1. Deploy to a staging environment
2. Run permission integration tests
3. Perform manual security testing with different user roles

## Related Issues
- Related to overall Backstage security hardening

---
*Discovered: 2026-02-03*
