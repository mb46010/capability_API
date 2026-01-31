# Domain Services: Capability Registry

## Overview
The `CapabilityRegistryService` is the system's authoritative source for what the system can *do*. it loads definitions from `config/capabilities/index.yaml` and provides lookup, validation, and discovery services.

## Key Features

### 1. Unified Registry
Loads all actions and flows into an O(1) lookup map. Use the `get_capability_registry()` factory to obtain the singleton instance.

### 2. Wildcard Expansion
Supports expanding patterns like `workday.hcm.*` into a set of all matching capability IDs. Used by the policy engine for broad permission grants.

### 3. Typo Detection & Suggestions
Provides fuzzy matching using `difflib` to suggest correct capability IDs when an invalid one is provided.

### 4. Validation
Includes methods to validate lists of capability strings (common in policy files) and returns structured error messages with suggestions.

## Integration Points
- **Policy Loader**: Validates policy files at startup.
- **Action Service**: Validates incoming API requests and handles deprecation warnings.
- **CLI Tool**: Exposes registry data for humans and CI/CD pipelines.