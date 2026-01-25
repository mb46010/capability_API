# Data Model: HR AI Platform Capability API

## Entities

### 1. Principal
Represents an identity interacting with the API.
- **ID**: UUID
- **Type**: enum (HUMAN, MACHINE, AI_AGENT)
- **OktaID**: string (subject claim from OIDC)
- **Metadata**: JSON (name, role, etc.)

### 2. Capability
A bounded operation (Action or Flow) exposed by the API.
- **Name**: string (unique identifier, e.g., `workday.get_employee`)
- **Type**: enum (ACTION, FLOW)
- **Schema**: JSON Schema (input/output requirements)
- **AuditPolicy**: enum (NONE, BASIC, VERBOSE)

### 3. Policy
The curated YAML rule defining access.
- **PrincipalType**: enum (HUMAN, MACHINE, AI_AGENT)
- **AllowedScopes**: list[string] (mappings to Capabilities)
- **Environment**: string (dev, prod)

### 4. ExecutionLog (Provenance)
- **LogID**: UUID
- **CapabilityName**: string
- **PrincipalID**: UUID
- **Timestamp**: ISO8601
- **Status**: enum (SUCCESS, FAILURE, PENDING)
- **InputData**: JSON (redacted if sensitive)
- **OutputData**: JSON
- **Provenance**: string (source of data, e.g., "MCP-Workday-CData")

## Relationships
- **Principal** <--- (many-to-many via Policy) ---> **Capability**
- **ExecutionLog** references **Principal** and **Capability**.
