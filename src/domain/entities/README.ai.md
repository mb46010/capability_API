# Domain Entities: Capabilities

## Overview
This module defines the core data structures for the Capability Registry. These Pydantic models represent the single source of truth for all system capabilities.

## Key Models

### `CapabilityEntry`
Represents a single atomic capability (Action or Flow).
- **id**: Unique string identifier (e.g. `workday.hcm.get_employee`)
- **domain**: Functional domain (e.g. `workday.hcm`)
- **type**: `action` (sync) or `flow` (async)
- **sensitivity**: Data sensitivity classification
- **deprecated**: Boolean flag for soft deprecation

### `CapabilityRegistry`
Root container for the entire registry.
- **version**: Schema version
- **metadata**: Ownership and timestamp info
- **capabilities**: List of `CapabilityEntry` objects

## Usage
These models are primarily used by:
1. `CapabilityRegistryService` (to load/validate YAML)
2. `PolicyLoader` (to validate policy references)
3. `ActionService` (to validate runtime requests)