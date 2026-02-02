# Bug: Backstage Catalog Not Loading API Entities

**Date**: 2026-02-02
**Status**: **RESOLVED**
**Priority**: High
**Component**: Governance/Backstage
**Resolution Date**: 2026-02-02

## Description
Despite correct configuration and file generation, the Backstage catalog (`hr-nexus`) refused to load or display entities of `kind: API`. The main `Component` (capability-api"), `System` ("hr-platform"), and `Group` ("platform-engineering") appeared correctly, but the ~23 API entities representing the capabilities were missing from the Catalog view, even when filtering by "All".

## Root Causes

### 1. Invalid API Type (Primary Issue)
The API entities were using custom `spec.type` values (`action` and `flow`) instead of Backstage-standard API types. Backstage only recognizes:
- `openapi`
- `asyncapi`
- `graphql`
- `grpc`

**Location**: `scripts/templates/catalog-info.yaml.j2:25`

### 2. YAML Parsing Error (Secondary Issue)
The generated `catalog-all.yaml` contained a multiline Mermaid flowchart that wasn't properly indented for YAML, causing parsing errors at line 995.

**Error**: `YAMLParseError: Implicit keys need to be on a single line at line 995, column 3`

### 3. Invalid Links URL Format (Tertiary Issue)
The `metadata.links[].url` field used relative paths (`/docs/...`) instead of absolute URLs, causing policy check failures.

## Solution

Modified `scripts/templates/catalog-info.yaml.j2` with three fixes:

1. **Changed `spec.type` to standard Backstage API type**:
   ```diff
   - spec.type: {{ capability.type }}
   + spec.type: openapi
   ```

2. **Fixed definition field to use valid OpenAPI 3.0 spec**:
   ```yaml
   definition: |
     openapi: 3.0.0
     info:
       title: {{ capability.name }}
       description: {{ capability.description or "" }}
       version: 1.0.0
     paths:
       /{action}:
         post:
           summary: {{ capability.name }}
           operationId: {{ capability.id | replace('.', '_') }}
           tags:
           ...
   ```

3. **Fixed links to use absolute URLs**:
   ```diff
   - url: /docs/default/component/capability-api/governance
   + url: http://localhost:3000/docs/default/component/capability-api/governance
   ```

## Verification

After regenerating `catalog-all.yaml` and restarting Backstage:
- ✅ All 23 API entities are now detected
- ✅ No YAML parsing errors
- ✅ No policy check failures
- ✅ Entities should now be visible in Catalog UI at http://localhost:3000

## Files Modified

- `scripts/templates/catalog-info.yaml.j2` - Updated template
- `catalog-all.yaml` - Regenerated with fixes

## Commands Used

```bash
# Regenerate catalog with fixed template
python3 scripts/generate_catalog.py --monolith

# Validate YAML
python3 -c "import yaml; yaml.safe_load_all(open('catalog-all.yaml')); print('Valid!')"

# Restart Backstage
cd hr-nexus && yarn start
```

## Lessons Learned

1. **Backstage API types are strict**: Custom types like `action` or `flow` are not supported. Must use standard API specification types.

2. **YAML multiline strings need careful indentation**: When embedding complex content (like Mermaid diagrams) in YAML, ensure proper indentation or avoid altogether.

3. **Backstage entity links require absolute URLs**: Relative paths in `metadata.links[].url` fail validation.

4. **Check Backstage logs for silent failures**: The catalog processor logs detailed error messages that aren't shown in the UI.

## Testing Recommendations

Navigate to http://localhost:3000/catalog and filter by:
- Kind: API
- Owner: platform-engineering

All 23 capability APIs should now be visible.
