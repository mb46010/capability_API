# Research: HR AI Platform Capability API

## Technical Decisions

### Decision: Python 3.11+ & FastAPI
- **Rationale**: Python-Native requirement from Constitution. FastAPI provides excellent OpenAPI support and type safety via Pydantic.
- **Alternatives considered**: Flask (less idiomatic for modern APIs), Django (too heavy for a "Capability API" focus).

### Decision: Pydantic V2 for Data Contracts
- **Rationale**: Strict validation and self-documenting schemas as per Constitution Article VI.
- **Alternatives considered**: Marshmallow (older, less integrated with FastAPI).

### Decision: Hexagonal Architecture (Storage Port)
- **Rationale**: Mandatory by Constitution Article II. Logic will be agnostic of storage (Local FS vs S3).

### Decision: AWS Step Functions (Standard) for Flows
- **Rationale**: Requirement from Product framing. Provides reliable state management for long-running HR processes.

## Items Needing Clarification

### 1. Okta OIDC Integration
- **Question**: Which Python library is best for validating Okta tokens and handling multiple principal types (Human, Machine, AI)?
- **Research Task**: Evaluate `authlib` vs `python-jose` vs Okta's own SDK.

### 2. Capability-based Authorization
- **Question**: How to implement scope-to-action mapping dynamically using the "policy YAML"?
- **Research Task**: Look into FastAPI dependencies for RBAC/ABAC patterns that can consume YAML policies.

### 3. Local Flow Runner
- **Question**: Is there a lightweight local alternative to "LocalStack Step Functions" for mock execution?
- **Research Task**: Investigate if a simple state-machine runner in Python is sufficient for "local-first" development.

### 4. MCP Server Treatment
- **Question**: How to treat MCP servers (e.g., Workday) as "strictly connectors"?
- **Research Task**: Research the MCP SDK for Python to see how to wrap servers in a Capability API layer.

### 5. Backstage Local Integration
- **Question**: How to automate the registration of the "Capability API" in a local Backstage instance?
- **Research Task**: Research Backstage software templates and Catalog API.
