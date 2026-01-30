# Architectural Guide: Capability API

This document provides a high-level overview of the HR AI Platform's Capability API system design.

## System Context (C4 Level 1)

The Capability API serves as the central orchestration layer between AI Agents/HR Applications and external HR systems like Workday.

```mermaid
C4Context
  title System Context diagram for Capability API
  
  Person(agent, "AI Agent", "Automated reasoning engine requesting HR actions")
  Person(admin, "HR Admin", "Human user managing policies and workflows")
  
  System(capapi, "Capability API", "Governed surface exposing deterministic actions and flows")
  
  System_Ext(workday, "Workday", "Core HRIS containing employee and payroll records")
  System_Ext(okta, "Okta", "Identity Provider for OIDC authentication")

  Rel(agent, capapi, "Invokes Actions/Flows", "HTTPS/JSON + JWT")
  Rel(admin, capapi, "Manages Policies", "YAML/CLI")
  
  Rel(capapi, workday, "Integrates with", "REST API")
  Rel(capapi, okta, "Validates Tokens against", "JWKS")
```

## Containers (C4 Level 2)

The system follows a **Hexagonal Architecture** (Ports and Adapters) to ensure the core business logic remains isolated from infrastructure concerns.

```mermaid
C4Container
  title Container diagram for Capability API
  
  Container_Boundary(api_boundary, "API Layer") {
    Container(routes, "API Routes", "FastAPI", "Request handling and Auth injection")
  }

  Container_Boundary(core_boundary, "Protected Domain Core") {
    Container(action_service, "Action Service", "Python", "Policy evaluation and action routing")
    Container(flow_service, "Flow Service", "Python", "Workflow orchestration")
    Container(policy_engine, "Policy Engine", "Python", "Capability-based authorization logic")
  }

  Container_Boundary(adapter_boundary, "Implementation Adapters") {
    Container(workday_adapter, "Workday Adapter", "Python", "Simulated or Real Workday connector")
    Container(auth_adapter, "Auth Adapter", "Python", "Token verification logic")
    Container(fs_adapter, "Filesystem Adapter", "Python", "Local storage for policies and flows")
    Container(mcp_server, "HR MCP Server", "FastMCP 3.0", "AI-agent gateway with RBAC")
  }

  Rel(mcp_server, routes, "Invokes", "HTTPS/JSON")

  Rel(routes, action_service, "Calls", "Internal")
  Rel(routes, flow_service, "Calls", "Internal")
  
  Rel(action_service, policy_engine, "Uses", "Logic")
  
  Rel(action_service, workday_adapter, "Uses", "Connector Port")
  Rel(flow_service, fs_adapter, "Uses", "Flow Runner Port")
  Rel(routes, auth_adapter, "Uses", "Token Verifier Port")
```

## Port & Adapter Mappings

| Port (Interface) | Adapter (Implementation) | Purpose |
|------------------|--------------------------|---------|
| `ConnectorPort` | `WorkdaySimulator` | External HR system integration |
| `FlowRunnerPort` | `LocalFlowRunnerAdapter` | Long-running process execution |
| `PolicyLoaderPort`| `FilePolicyLoaderAdapter`| Policy document persistence |
| `TokenVerifier` | `MockTokenVerifier` | Identity validation |

## Module Documentation

For detailed information on specific system components, refer to the following module guides:

- **[API Layer](modules/api_layer.md)**: Entry points, routing, and dependencies.
- **[Domain Entities](modules/domain_entities.md)**: Core data models and audit protocols.
- **[Auth Adapter](modules/auth_adapter.md)**: OIDC simulation and token verification.
- **[Workday Simulator](modules/workday_adapter.md)**: Simulated HRIS implementation (HCM, Time, Payroll).
- **[Filesystem Adapter](modules/filesystem_adapter.md)**: Policy loading and flow execution.

## Core Principles
1. **The Sanctuary**: The `domain/` directory MUST NOT import from `adapters/` or `api/`.
2. **Deterministic Actions**: All actions must have explicit Pydantic schemas and predictable outcomes.
3. **Audit by Design**: Every operation generates provenance metadata tracked via the `ActionResponse`.
