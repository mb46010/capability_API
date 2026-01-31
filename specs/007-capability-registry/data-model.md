# Data Model - Capability Registry

## Entities

### CapabilityEntry
Represents a single executable capability (Action or Flow) in the system.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `id` | `str` | Unique identifier | Format: `domain.subdomain.action`. Must be unique across registry. |
| `name` | `str` | Human-readable name | Non-empty string. |
| `domain` | `str` | Domain namespace | e.g., `workday.hcm`. |
| `type` | `Enum` | `action` or `flow` | Restricted to `CapabilityType` enum. |
| `sensitivity` | `Enum` | Data sensitivity level | `low`, `medium`, `high`, `critical`. |
| `requires_mfa` | `bool` | High-assurance requirement | Default `False`. |
| `tags` | `List[str]` | Classification tags | Optional list of strings. |
| `description` | `str` | Detailed documentation | Optional. |
| `deprecated` | `bool` | Deprecation status | Default `False`. |

### CapabilityRegistry
The root container for all capabilities.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| `version` | `str` | Schema version | e.g., "1.0". |
| `metadata` | `Object` | Registry metadata | Owner, last_updated. |
| `capabilities` | `List[CapabilityEntry]` | List of defined capabilities | Must have unique IDs. |

## Relationships

- A `CapabilityRegistry` contains 1..N `CapabilityEntry` items.
- A `Policy` (external entity) references `CapabilityEntry` by `id` (string reference).

## Schema Definitions (Pydantic)

```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class CapabilityType(str, Enum):
    ACTION = "action"
    FLOW = "flow"

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CapabilityEntry(BaseModel):
    id: str
    name: str
    domain: str
    type: CapabilityType
    sensitivity: SensitivityLevel
    requires_mfa: bool = False
    tags: List[str] = []
    description: Optional[str] = None
    deprecated: bool = False

class CapabilityRegistryMetadata(BaseModel):
    last_updated: str
    owner: str
    description: str

class CapabilityRegistry(BaseModel):
    version: str
    metadata: CapabilityRegistryMetadata
    capabilities: List[CapabilityEntry]
```
