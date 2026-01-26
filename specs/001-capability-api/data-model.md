# Data Model: Capability API

**Status**: Draft
**Date**: 2026-01-26

## 1. Policy Domain
*Based on `schemas/policy-schema.json`*

The Policy is the core governance artifact.

### Entities

#### `AccessPolicy` (Root)
- `version`: str
- `metadata`: `PolicyMetadata`
- `principals`: Dict[str, `PrincipalDefinition`]
- `capability_groups`: Dict[str, List[str]]
- `policies`: List[`PolicyRule`]

#### `PolicyRule`
- `name`: str
- `principal`: str | `PrincipalDefinition`
- `capabilities`: List[str] | str (Group Ref)
- `environments`: List[`Environment`]
- `effect`: "ALLOW"
- `conditions`: `PolicyConditions` (Optional)
- `audit`: "BASIC" | "VERBOSE"

#### `PrincipalDefinition`
- `type`: "HUMAN" | "MACHINE" | "AI_AGENT"
- `okta_subject`: str (Optional)
- `okta_group`: str (Optional)

## 2. API Interaction Models

### Action Execution

#### `ActionRequest`
```python
class ActionRequest(BaseModel):
    parameters: Dict[str, Any]  # Arguments for the action
    dry_run: bool = False       # If supported by connector
```

#### `ActionResponse` (JSON with Provenance)
```python
class Provenance(BaseModel):
    source: str
    timestamp: datetime
    trace_id: str
    latency_ms: float
    actor: str  # Principal who executed it

class ActionResponse(BaseModel):
    data: Dict[str, Any] | List[Any]
    meta: Dict[str, Provenance]
```

### Flow Orchestration

#### `FlowStartRequest`
```python
class FlowStartRequest(BaseModel):
    parameters: Dict[str, Any]
    callback_url: str | None = None  # Optional webhook for completion
```

#### `FlowStatusResponse`
```python
class FlowStatusResponse(BaseModel):
    flow_id: str
    status: "RUNNING" | "COMPLETED" | "FAILED" | "WAITING_FOR_INPUT"
    start_time: datetime
    current_step: str | None
    result: Dict[str, Any] | None
    error: str | None
```