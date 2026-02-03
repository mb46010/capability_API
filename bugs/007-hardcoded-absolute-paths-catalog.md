# BUG-007: Hardcoded Absolute Paths in Backstage Catalog Configuration

## Severity
🟡 MEDIUM

## Location
- **File(s)**: `hr-nexus/app-config.yaml`
- **Line(s)**: 81-92

## Issue Description
The Backstage catalog configuration contains hardcoded absolute paths that are specific to a single developer's machine:

```yaml
# ❌ PROBLEMATIC - Hardcoded paths
catalog:
  locations:
    - type: file
      target: /home/marco/Code/Experiments/capability_API/catalog-info.yaml
    - type: file
      target: /home/marco/Code/Experiments/capability_API/catalog/platform-engineering.yaml
    - type: file
      target: /home/marco/Code/Experiments/capability_API/catalog-all.yaml
```

These paths will not exist on other developers' machines or in any deployment environment, causing:
- Catalog loading failures
- CI/CD pipeline errors
- Onboarding friction for new developers

## Impact
- **Broken deployments**: Application fails in any environment except the original developer's machine
- **CI/CD failures**: Automated builds will fail when catalog can't be loaded
- **Poor portability**: Other developers cannot run the application locally without modification

## Root Cause
The configuration was created on a specific machine and committed without making the paths relative or environment-configurable. This is a common mistake when transitioning from local development to team collaboration.

## How to Fix

### Code Changes
Use relative paths or URL-based locations:

```yaml
# ✅ FIXED - Use relative paths (relative to backstage working directory)
catalog:
  locations:
    - type: file
      target: ../catalog-info.yaml
    - type: file
      target: ../catalog/platform-engineering.yaml
    - type: file
      target: ../catalog-all.yaml

# ✅ ALTERNATIVE - Use environment variable
catalog:
  locations:
    - type: file
      target: ${CATALOG_ROOT}/catalog-info.yaml
```

### Steps
1. Update `hr-nexus/app-config.yaml` to use relative paths
2. Update `hr-nexus/app-config.production.yaml` to use appropriate production paths
3. Add `CATALOG_ROOT` environment variable support if needed
4. Update documentation for local development setup
5. Verify paths work from the backstage working directory

## Verification

### Test Cases
1. Run Backstage from `hr-nexus/` directory - catalog should load
2. Run in CI/CD environment - catalog should load
3. Clone repo fresh and run - should work without modification

### Verification Steps
1. Delete `.git` and re-clone the repository
2. Follow the README setup instructions
3. Verify Backstage catalog loads correctly

## Related Issues
- None

---
*Discovered: 2026-02-03*
