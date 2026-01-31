# Capability Registry PRD - Option C: Minimal Registry (YAML Index + Validator)

**Version**: 1.0  
**Status**: Ready for Implementation  
**Owner**: HR AI Platform Governance Team  
**Target**: Pre-Demo Foundation / Phase 1 Deployment  
**Estimated Effort**: 6-8 hours

---

## Executive Summary

**Problem**: The HR AI Platform currently has no single source of truth for capabilities. This creates three critical gaps:

1. **Policy Validation Gap**: Policies can reference non-existent capabilities without detection until runtime
2. **Maintenance Burden**: Adding new capabilities requires manual updates in 3+ locations (ActionService, MCP Server, Policy)
3. **Documentation Drift**: No machine-readable catalog for developers, AI agents, or governance tools

**Solution**: Implement a minimal YAML-based capability registry that serves as the canonical source of truth. This registry validates policy references at startup, enables capability discovery, and provides a foundation for future governance tooling (Backstage.io).

**Scope**: This PRD covers **Option C** - a pragmatic, production-ready registry that balances governance needs with implementation speed. It does NOT include auto-generation of MCP tools or full OpenAPI spec generation (deferred to Phase 2).

---

## Goals & Non-Goals

### Goals ✅

1. **Startup Policy Validation**: Catch typos in policy files before deployment
2. **Single Source of Truth**: Centralized registry that all components reference
3. **Capability Discovery**: Enable programmatic queries for "what capabilities exist"
4. **Future-Proof Foundation**: Structure supports Phase 2 enhancements (auto-generation, Backstage)
5. **Zero Runtime Overhead**: Registry loaded at startup, no performance impact

### Non-Goals ❌

1. **Auto-Generation**: MCP tools and route handlers remain manually coded (Phase 2)
2. **Full Schema Specifications**: No parameter/return schemas (use Pydantic models)
3. **REST API**: No `/catalog/capabilities` endpoint (file-based only)
4. **Composite Capabilities**: No multi-step workflow definitions (Phase 3)
5. **Versioning**: No `v1/v2` capability versioning (single version per capability)

---

## Background & Context

### Current State (Pain Points)

**Problem 1: Policy Typos Fail at Runtime**
```yaml
# config/policy-workday.yaml (TYPO in capability name)
policies:
  - name: "employee-self-service"
    capabilities:
      - "workday.hcm.get_employe"  # ❌ Should be get_employee
```

**Current Behavior**:
- ✅ Policy loads successfully at startup
- ❌ User gets 403 "Access denied" at runtime (capability not in KNOWN_CAPABILITIES)
- ❌ No indication that the policy contains a typo

**Desired Behavior**:
- ❌ Server fails to start with error: `Policy 'employee-self-service' references unknown capability 'workday.hcm.get_employe'`

---

**Problem 2: Scattered Capability Definitions**

To add a new capability (e.g., `workday.hcm.update_job_title`), developers must update:

1. `src/domain/services/action_service.py` (KNOWN_CAPABILITIES dict)
2. `src/adapters/workday/services/hcm.py` (implementation)
3. `src/mcp/server.py` (MCP tool definition)
4. `config/policy-workday.yaml` (authorization rules)

**Risk**: Forgetting to update any location causes runtime failures or security gaps.

---

**Problem 3: No Capability Discovery**

**Use Cases Blocked**:
- MCP client asks: "What tools can I use?" → No programmatic answer
- Policy auditor asks: "What capabilities exist in prod?" → Must read source code
- Backstage dashboard asks: "Show me all HCM capabilities" → No structured data

---

### Architecture Context

**Current Architecture**:
```
┌──────────────────┐
│ Policy YAML      │ ← References capabilities as strings
└────────┬─────────┘
         │
         ↓ (no validation)
┌──────────────────┐
│ PolicyEngine     │ ← Trusts capability strings exist
└────────┬─────────┘
         │
         ↓ (runtime check)
┌──────────────────┐
│ ActionService    │ ← Has KNOWN_CAPABILITIES dict (hardcoded)
└────────┬─────────┘
         │
         ↓
┌──────────────────┐
│ Workday Adapter  │ ← Implements capabilities
└──────────────────┘
```

**Target Architecture**:
```
┌──────────────────────┐
│ Capability Registry  │ ← Single source of truth (YAML)
│ (index.yaml)         │
└──────┬───────────────┘
       │
       ├──→ PolicyLoader (validates references at startup)
       ├──→ ActionService (validates requests at runtime)
       ├──→ MCP Server (future: auto-generate tools)
       └──→ Backstage (future: governance dashboard)
```

---

## Requirements

### FR-001: Registry File Structure

**Specification**: Registry stored as YAML file(s) with hierarchical organization.

**Directory Structure**:
```
config/capabilities/
├── index.yaml                      # Main registry (all capabilities)
├── workday/
│   ├── hcm.yaml                   # HCM domain capabilities
│   ├── time.yaml                  # Time management capabilities
│   └── payroll.yaml               # Payroll capabilities
└── hr/
    └── flows.yaml                 # Long-running workflows
```

**Primary Registry**: `config/capabilities/index.yaml`
```yaml
version: "1.0"
metadata:
  last_updated: "2026-01-31"
  owner: "hr-platform-team"
  description: "Canonical registry of all HR AI Platform capabilities"

capabilities:
  # HCM Domain
  - id: "workday.hcm.get_employee"
    name: "Get Employee Profile"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "medium"
    tags: ["read-only", "hcm", "pii"]
    
  - id: "workday.hcm.get_manager_chain"
    name: "Get Manager Chain"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "low"
    tags: ["read-only", "hcm"]
    
  - id: "workday.hcm.list_direct_reports"
    name: "List Direct Reports"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "medium"
    tags: ["read-only", "hcm", "manager-only"]
    
  - id: "workday.hcm.update_contact_info"
    name: "Update Contact Information"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "medium"
    tags: ["write", "hcm", "self-service"]
    
  - id: "workday.hcm.get_org_chart"
    name: "Get Organization Chart"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "low"
    tags: ["read-only", "hcm"]
  
  # Time Management Domain
  - id: "workday.time.get_balance"
    name: "Get PTO Balance"
    domain: "workday.time"
    type: "action"
    sensitivity: "low"
    tags: ["read-only", "time-off"]
    
  - id: "workday.time.request"
    name: "Request Time Off"
    domain: "workday.time"
    type: "action"
    sensitivity: "medium"
    tags: ["write", "time-off"]
    
  - id: "workday.time.cancel"
    name: "Cancel Time Off Request"
    domain: "workday.time"
    type: "action"
    sensitivity: "medium"
    tags: ["write", "time-off"]
    
  - id: "workday.time.approve"
    name: "Approve Time Off"
    domain: "workday.time"
    type: "action"
    sensitivity: "high"
    tags: ["write", "time-off", "manager-only"]
  
  # Payroll Domain
  - id: "workday.payroll.get_compensation"
    name: "Get Compensation Details"
    domain: "workday.payroll"
    type: "action"
    sensitivity: "critical"
    requires_mfa: true
    tags: ["read-only", "payroll", "pii", "mfa-required"]
    
  - id: "workday.payroll.get_pay_statement"
    name: "Get Pay Statement"
    domain: "workday.payroll"
    type: "action"
    sensitivity: "critical"
    requires_mfa: true
    tags: ["read-only", "payroll", "pii", "mfa-required"]
    
  - id: "workday.payroll.list_pay_statements"
    name: "List Pay Statements"
    domain: "workday.payroll"
    type: "action"
    sensitivity: "high"
    requires_mfa: true
    tags: ["read-only", "payroll", "mfa-required"]

  # Long-Running Flows
  - id: "hr.onboarding"
    name: "Employee Onboarding Flow"
    domain: "hr"
    type: "flow"
    sensitivity: "high"
    tags: ["workflow", "onboarding"]
    
  - id: "hr.offboarding"
    name: "Employee Offboarding Flow"
    domain: "hr"
    type: "flow"
    sensitivity: "high"
    tags: ["workflow", "offboarding"]
```

**Schema Definition** (`src/domain/entities/capability.py`):
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class CapabilityType(str, Enum):
    ACTION = "action"      # Synchronous operations
    FLOW = "flow"          # Long-running workflows
    COMPOSITE = "composite"  # Multi-step (Phase 2)

class SensitivityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class CapabilityEntry(BaseModel):
    id: str = Field(description="Unique capability identifier (e.g., workday.hcm.get_employee)")
    name: str = Field(description="Human-readable name")
    domain: str = Field(description="Domain/subdomain (e.g., workday.hcm)")
    type: CapabilityType = Field(description="Capability type (action, flow, composite)")
    sensitivity: SensitivityLevel = Field(description="Data sensitivity level")
    requires_mfa: bool = Field(default=False, description="Whether MFA is required")
    tags: List[str] = Field(default=[], description="Classification tags")
    description: Optional[str] = Field(None, description="Detailed description")
    deprecated: bool = Field(default=False, description="Whether capability is deprecated")
    
class CapabilityRegistryMetadata(BaseModel):
    last_updated: str
    owner: str
    description: str

class CapabilityRegistry(BaseModel):
    version: str
    metadata: CapabilityRegistryMetadata
    capabilities: List[CapabilityEntry]
```

**Acceptance Criteria**:
- ✅ Registry contains all 13 existing capabilities (11 actions + 2 flows)
- ✅ YAML validates against Pydantic schema
- ✅ Each capability has unique `id`
- ✅ Sensitivity levels align with policy requirements
- ✅ MFA-required capabilities flagged

---

### FR-002: Registry Loader Service

**Specification**: Service to load and query the capability registry.

**Implementation** (`src/domain/services/capability_registry.py`):
```python
import yaml
from pathlib import Path
from typing import List, Optional, Set
from functools import lru_cache
from src.domain.entities.capability import CapabilityRegistry, CapabilityEntry, CapabilityType

class CapabilityRegistryService:
    """
    Service for loading and querying the capability registry.
    
    Usage:
        registry = CapabilityRegistryService("config/capabilities/index.yaml")
        if registry.exists("workday.hcm.get_employee"):
            capability = registry.get("workday.hcm.get_employee")
    """
    
    def __init__(self, index_path: str = "config/capabilities/index.yaml"):
        self.index_path = Path(index_path)
        self._registry: Optional[CapabilityRegistry] = None
        self._capability_map: dict[str, CapabilityEntry] = {}
        self._load()
    
    def _load(self) -> None:
        """Load registry from YAML file."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"Capability registry not found: {self.index_path}")
        
        with open(self.index_path, "r") as f:
            data = yaml.safe_load(f)
        
        self._registry = CapabilityRegistry(**data)
        
        # Build lookup map for O(1) access
        self._capability_map = {cap.id: cap for cap in self._registry.capabilities}
        
        # Validate no duplicate IDs
        if len(self._capability_map) != len(self._registry.capabilities):
            raise ValueError("Duplicate capability IDs found in registry")
    
    def exists(self, capability_id: str) -> bool:
        """Check if a capability exists in the registry."""
        return capability_id in self._capability_map
    
    def get(self, capability_id: str) -> Optional[CapabilityEntry]:
        """Get a capability by ID."""
        return self._capability_map.get(capability_id)
    
    def get_all(self) -> List[CapabilityEntry]:
        """Get all capabilities."""
        return self._registry.capabilities
    
    def get_by_domain(self, domain: str) -> List[CapabilityEntry]:
        """Get all capabilities for a domain."""
        return [cap for cap in self._registry.capabilities if cap.domain == domain]
    
    def get_by_type(self, cap_type: CapabilityType) -> List[CapabilityEntry]:
        """Get all capabilities of a specific type."""
        return [cap for cap in self._registry.capabilities if cap.type == cap_type]
    
    def get_by_tag(self, tag: str) -> List[CapabilityEntry]:
        """Get all capabilities with a specific tag."""
        return [cap for cap in self._registry.capabilities if tag in cap.tags]
    
    def get_mfa_required(self) -> List[CapabilityEntry]:
        """Get all capabilities requiring MFA."""
        return [cap for cap in self._registry.capabilities if cap.requires_mfa]
    
    def matches_wildcard(self, pattern: str) -> Set[str]:
        """
        Expand wildcard patterns to matching capability IDs.
        
        Examples:
            "workday.*" → all workday capabilities
            "workday.hcm.*" → all HCM capabilities
            "*" → all capabilities
        """
        if pattern == "*":
            return set(self._capability_map.keys())
        
        if not pattern.endswith(".*"):
            # Exact match or invalid pattern
            return {pattern} if self.exists(pattern) else set()
        
        prefix = pattern[:-2]  # Remove ".*"
        
        # Match all capabilities starting with prefix
        matches = set()
        for cap_id in self._capability_map.keys():
            if cap_id.startswith(prefix):
                # Ensure boundary: workday.hcm matches workday.hcm.*, not workday.hcmx.*
                if len(cap_id) == len(prefix) or cap_id[len(prefix)] == ".":
                    matches.add(cap_id)
        
        return matches
    
    def validate_capability_list(self, capabilities: List[str]) -> List[str]:
        """
        Validate a list of capability strings (from policy).
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        for cap in capabilities:
            if cap.endswith(".*"):
                # Wildcard - check if domain exists
                matches = self.matches_wildcard(cap)
                if not matches:
                    errors.append(f"Wildcard pattern '{cap}' matches no capabilities")
            else:
                # Exact match
                if not self.exists(cap):
                    errors.append(f"Unknown capability: '{cap}'")
                    
                    # Suggest similar capabilities (typo detection)
                    similar = self._find_similar(cap)
                    if similar:
                        errors.append(f"  Did you mean: {', '.join(similar[:3])}")
        
        return errors
    
    def _find_similar(self, cap_id: str, max_distance: int = 2) -> List[str]:
        """Find capabilities with similar names (Levenshtein distance)."""
        from difflib import get_close_matches
        all_ids = list(self._capability_map.keys())
        return get_close_matches(cap_id, all_ids, n=3, cutoff=0.6)
    
    def reload(self) -> None:
        """Reload registry from disk (useful for development)."""
        self._load()


# Singleton instance for application-wide use
@lru_cache(maxsize=1)
def get_capability_registry(index_path: str = "config/capabilities/index.yaml") -> CapabilityRegistryService:
    """Get singleton registry instance."""
    return CapabilityRegistryService(index_path)
```

**Acceptance Criteria**:
- ✅ Registry loads from YAML at initialization
- ✅ `exists()` returns correct results for valid/invalid IDs
- ✅ Wildcard matching works (`workday.*`, `workday.hcm.*`)
- ✅ Validation detects typos and suggests corrections
- ✅ Query methods filter by domain/type/tag
- ✅ Thread-safe singleton pattern

---

### FR-003: Startup Policy Validation

**Specification**: Policy loader must validate capability references against registry.

**Implementation** (`src/adapters/filesystem/policy_loader.py`):
```python
import yaml
from pathlib import Path
from src.domain.ports.policy_loader import PolicyLoaderPort
from src.domain.entities.policy import AccessPolicy
from src.domain.services.capability_registry import get_capability_registry

class FilePolicyLoaderAdapter(PolicyLoaderPort):
    def __init__(self, policy_path: str, registry_path: str = "config/capabilities/index.yaml"):
        self.policy_path = Path(policy_path)
        self.registry = get_capability_registry(registry_path)

    def load_policy(self) -> AccessPolicy:
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Policy file not found at {self.policy_path}")
        
        with open(self.policy_path, "r") as f:
            data = yaml.safe_load(f)
            
        policy = AccessPolicy(**data)
        
        # Validate policy references (principals, groups)
        validation_errors = policy.validate_references()
        if validation_errors:
            raise ValueError(f"Policy validation failed:\n" + "\n".join(validation_errors))
        
        # NEW: Validate capability references
        capability_errors = self._validate_capabilities(policy)
        if capability_errors:
            raise ValueError(
                f"Policy capability validation failed:\n" + 
                "\n".join(capability_errors)
            )
            
        return policy
    
    def _validate_capabilities(self, policy: AccessPolicy) -> List[str]:
        """Validate all capability references in the policy."""
        errors = []
        
        for rule in policy.policies:
            # Expand capabilities (handle groups)
            if isinstance(rule.capabilities, str):
                # It's a group reference
                capabilities = policy.capability_groups.get(rule.capabilities, [])
            else:
                capabilities = rule.capabilities
            
            # Validate each capability
            rule_errors = self.registry.validate_capability_list(capabilities)
            if rule_errors:
                errors.append(f"Policy '{rule.name}':")
                errors.extend([f"  {err}" for err in rule_errors])
        
        # Validate capability groups themselves
        for group_name, capabilities in policy.capability_groups.items():
            group_errors = self.registry.validate_capability_list(capabilities)
            if group_errors:
                errors.append(f"Capability group '{group_name}':")
                errors.extend([f"  {err}" for err in group_errors])
        
        return errors
```

**Error Output Example**:
```
$ uvicorn src.main:app --reload
ValueError: Policy capability validation failed:
Policy 'employee-self-service':
  Unknown capability: 'workday.hcm.get_employe'
    Did you mean: workday.hcm.get_employee
Policy 'admin-full-access':
  Wildcard pattern 'calendar.*' matches no capabilities
Capability group 'all_actions':
  Unknown capability: 'workday.payroll.get_salary'
    Did you mean: workday.payroll.get_compensation
```

**Acceptance Criteria**:
- ✅ Server fails to start if policy references invalid capabilities
- ✅ Error messages include specific policy/group names
- ✅ Typo suggestions displayed (Levenshtein distance)
- ✅ Wildcard patterns validated
- ✅ All policies validated before server starts

---

### FR-004: Runtime Capability Validation

**Specification**: ActionService must validate requests against registry.

**Implementation** (`src/domain/services/action_service.py`):
```python
from src.domain.services.capability_registry import get_capability_registry

class ActionService:
    def __init__(self, policy_engine: PolicyEngine, connector: ConnectorPort):
        self.policy_engine = policy_engine
        self.connector = connector
        self.registry = get_capability_registry()  # NEW
    
    def _validate_capability(self, domain: str, action: str):
        """Validate capability exists in registry."""
        capability_id = f"{domain}.{action}"
        
        # Try full capability ID first
        if self.registry.exists(capability_id):
            return
        
        # Try with subdomain expansion (workday → workday.hcm)
        if domain == "workday":
            for subdomain in ["hcm", "time", "payroll"]:
                full_id = f"workday.{subdomain}.{action}"
                if self.registry.exists(full_id):
                    return  # Valid
        
        # Not found - provide helpful error
        similar = self.registry._find_similar(capability_id)
        if similar:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown capability: {capability_id}. Did you mean: {', '.join(similar[:3])}?"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown capability: {capability_id}"
            )
```

**Acceptance Criteria**:
- ✅ Unknown capabilities return 400 (not 403)
- ✅ Error messages suggest similar capabilities
- ✅ Validation uses registry (not hardcoded KNOWN_CAPABILITIES)
- ✅ Runtime performance unaffected (registry loaded once)

---

### FR-005: Configuration Validator Integration

**Specification**: Config validator must check registry file exists.

**Implementation** (`src/lib/config_validator.py`):
```python
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.domain.services.capability_registry import CapabilityRegistryService

class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    ENVIRONMENT: str = Field(default="local", description="Deployment environment")
    POLICY_PATH: str = Field(default="config/policy-workday.yaml", description="Path to policy YAML")
    CAPABILITY_REGISTRY_PATH: str = Field(
        default="config/capabilities/index.yaml",
        description="Path to capability registry"
    )
    
    @field_validator("POLICY_PATH", "CAPABILITY_REGISTRY_PATH")
    @classmethod
    def validate_file_exists(cls, v: str) -> str:
        path = Path(v)
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {v}")
        return v
    
    @model_validator(mode='after')
    def validate_policy_and_registry(self):
        """Cross-validate policy against capability registry."""
        # Import here to avoid circular dependency
        from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
        
        try:
            loader = FilePolicyLoaderAdapter(
                policy_path=self.POLICY_PATH,
                registry_path=self.CAPABILITY_REGISTRY_PATH
            )
            # This will raise ValueError if validation fails
            policy = loader.load_policy()
            
            print(f"✅ Policy validation passed ({len(policy.policies)} rules)")
            
        except Exception as e:
            print(f"❌ Configuration validation failed:")
            print(f"   {str(e)}")
            raise
        
        return self

# Create global instance (validates on import)
settings = AppSettings()
```

**Startup Output**:
```
$ uvicorn src.main:app --reload
✅ Capability registry loaded (13 capabilities)
✅ Policy validation passed (8 rules)
INFO:     Started server process [12345]
```

**Acceptance Criteria**:
- ✅ Server fails to start if registry missing
- ✅ Server fails to start if policy invalid
- ✅ Startup logs show validation results
- ✅ No circular import issues

---

### FR-006: CLI Tools for Registry Management

**Specification**: Command-line tools for registry inspection and validation.

**Implementation** (`scripts/capability-registry`):
```bash
#!/usr/bin/env python3
"""
Capability Registry CLI Tool

Usage:
    ./scripts/capability-registry list [--domain=<domain>] [--type=<type>]
    ./scripts/capability-registry validate
    ./scripts/capability-registry check-policy <policy-file>
    ./scripts/capability-registry deps <capability-id>
    ./scripts/capability-registry stats
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain.services.capability_registry import get_capability_registry
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from tabulate import tabulate


def cmd_list(args):
    """List capabilities with optional filtering."""
    registry = get_capability_registry(args.registry)
    
    capabilities = registry.get_all()
    
    # Apply filters
    if args.domain:
        capabilities = [c for c in capabilities if c.domain == args.domain]
    if args.type:
        capabilities = [c for c in capabilities if c.type == args.type]
    if args.tag:
        capabilities = [c for c in capabilities if args.tag in c.tags]
    
    # Format output
    if args.format == "table":
        headers = ["ID", "Name", "Type", "Sensitivity", "MFA"]
        rows = [
            [c.id, c.name, c.type.value, c.sensitivity.value, "✓" if c.requires_mfa else ""]
            for c in capabilities
        ]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
    
    elif args.format == "json":
        import json
        data = [c.model_dump() for c in capabilities]
        print(json.dumps(data, indent=2))
    
    else:  # simple
        for c in capabilities:
            print(c.id)


def cmd_validate(args):
    """Validate registry structure."""
    try:
        registry = get_capability_registry(args.registry)
        capabilities = registry.get_all()
        
        print(f"✅ Registry is valid")
        print(f"   Version: {registry._registry.version}")
        print(f"   Capabilities: {len(capabilities)}")
        print(f"   Domains: {len(set(c.domain for c in capabilities))}")
        
        # Check for potential issues
        warnings = []
        
        # Check for missing descriptions
        no_desc = [c.id for c in capabilities if not c.description]
        if no_desc:
            warnings.append(f"⚠️  {len(no_desc)} capabilities missing descriptions")
        
        # Check for deprecated capabilities
        deprecated = [c.id for c in capabilities if c.deprecated]
        if deprecated:
            warnings.append(f"⚠️  {len(deprecated)} deprecated capabilities: {', '.join(deprecated)}")
        
        if warnings:
            print("\nWarnings:")
            for w in warnings:
                print(f"  {w}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Validation failed: {str(e)}")
        sys.exit(1)


def cmd_check_policy(args):
    """Validate policy against registry."""
    try:
        loader = FilePolicyLoaderAdapter(
            policy_path=args.policy_file,
            registry_path=args.registry
        )
        policy = loader.load_policy()
        
        print(f"✅ Policy is valid")
        print(f"   Policies: {len(policy.policies)}")
        print(f"   Capability Groups: {len(policy.capability_groups)}")
        
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ Policy validation failed:")
        print(f"   {str(e)}")
        sys.exit(1)


def cmd_deps(args):
    """Show dependencies for a capability (future: composite capabilities)."""
    registry = get_capability_registry(args.registry)
    capability = registry.get(args.capability_id)
    
    if not capability:
        print(f"❌ Capability not found: {args.capability_id}")
        sys.exit(1)
    
    print(f"Capability: {capability.id}")
    print(f"Name: {capability.name}")
    print(f"Type: {capability.type.value}")
    print(f"Domain: {capability.domain}")
    print(f"Sensitivity: {capability.sensitivity.value}")
    print(f"MFA Required: {'Yes' if capability.requires_mfa else 'No'}")
    print(f"Tags: {', '.join(capability.tags)}")
    
    # Future: Show composite capability dependencies
    if capability.type == "composite":
        print("\n⚠️  Composite capabilities not yet supported")


def cmd_stats(args):
    """Show registry statistics."""
    registry = get_capability_registry(args.registry)
    capabilities = registry.get_all()
    
    # Count by type
    by_type = {}
    for c in capabilities:
        by_type[c.type.value] = by_type.get(c.type.value, 0) + 1
    
    # Count by domain
    by_domain = {}
    for c in capabilities:
        by_domain[c.domain] = by_domain.get(c.domain, 0) + 1
    
    # Count by sensitivity
    by_sensitivity = {}
    for c in capabilities:
        by_sensitivity[c.sensitivity.value] = by_sensitivity.get(c.sensitivity.value, 0) + 1
    
    print("Capability Registry Statistics")
    print("=" * 40)
    print(f"Total Capabilities: {len(capabilities)}")
    print()
    
    print("By Type:")
    for t, count in sorted(by_type.items()):
        print(f"  {t:12} {count:3}")
    print()
    
    print("By Domain:")
    for d, count in sorted(by_domain.items()):
        print(f"  {d:20} {count:3}")
    print()
    
    print("By Sensitivity:")
    for s, count in sorted(by_sensitivity.items()):
        print(f"  {s:12} {count:3}")
    print()
    
    mfa_count = len([c for c in capabilities if c.requires_mfa])
    print(f"MFA Required: {mfa_count}")
    
    deprecated_count = len([c for c in capabilities if c.deprecated])
    if deprecated_count:
        print(f"Deprecated: {deprecated_count}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capability Registry CLI")
    parser.add_argument(
        "--registry",
        default="config/capabilities/index.yaml",
        help="Path to capability registry"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # list command
    list_parser = subparsers.add_parser("list", help="List capabilities")
    list_parser.add_argument("--domain", help="Filter by domain")
    list_parser.add_argument("--type", help="Filter by type (action, flow)")
    list_parser.add_argument("--tag", help="Filter by tag")
    list_parser.add_argument("--format", choices=["simple", "table", "json"], default="table")
    
    # validate command
    validate_parser = subparsers.add_parser("validate", help="Validate registry")
    
    # check-policy command
    check_parser = subparsers.add_parser("check-policy", help="Validate policy against registry")
    check_parser.add_argument("policy_file", help="Path to policy YAML file")
    
    # deps command
    deps_parser = subparsers.add_parser("deps", help="Show capability dependencies")
    deps_parser.add_argument("capability_id", help="Capability ID")
    
    # stats command
    stats_parser = subparsers.add_parser("stats", help="Show registry statistics")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Dispatch to command handler
    {
        "list": cmd_list,
        "validate": cmd_validate,
        "check-policy": cmd_check_policy,
        "deps": cmd_deps,
        "stats": cmd_stats,
    }[args.command](args)
```

**Usage Examples**:
```bash
# List all capabilities
./scripts/capability-registry list

# List HCM capabilities
./scripts/capability-registry list --domain workday.hcm

# List MFA-required capabilities
./scripts/capability-registry list --tag mfa-required --format json

# Validate registry structure
./scripts/capability-registry validate

# Check policy against registry
./scripts/capability-registry check-policy config/policy-workday.yaml

# Show capability details
./scripts/capability-registry deps workday.payroll.get_compensation

# Show statistics
./scripts/capability-registry stats
```

**Acceptance Criteria**:
- ✅ CLI validates registry structure
- ✅ CLI checks policy against registry
- ✅ CLI filters/queries capabilities
- ✅ CLI generates statistics report
- ✅ Output formats: table, JSON, simple

---

### FR-007: CI/CD Integration

**Specification**: Registry validation runs in CI pipeline.

**GitHub Actions Workflow** (`.github/workflows/validate-registry.yml`):
```yaml
name: Validate Capability Registry

on:
  pull_request:
    paths:
      - 'config/capabilities/**'
      - 'config/policy-*.yaml'
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Validate registry structure
        run: |
          ./scripts/capability-registry validate
      
      - name: Validate policy against registry
        run: |
          ./scripts/capability-registry check-policy config/policy-workday.yaml
      
      - name: Check for duplicate capability IDs
        run: |
          python -c "
          import yaml
          with open('config/capabilities/index.yaml') as f:
              data = yaml.safe_load(f)
          ids = [c['id'] for c in data['capabilities']]
          if len(ids) != len(set(ids)):
              print('❌ Duplicate capability IDs found')
              exit(1)
          print('✅ No duplicate IDs')
          "
      
      - name: Generate registry report
        run: |
          ./scripts/capability-registry stats > registry-report.txt
          cat registry-report.txt
      
      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: registry-report
          path: registry-report.txt
```

**Pre-Commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Validate registry before commit

echo "Validating capability registry..."
./scripts/capability-registry validate || {
    echo "❌ Registry validation failed - commit rejected"
    exit 1
}

echo "Validating policy against registry..."
./scripts/capability-registry check-policy config/policy-workday.yaml || {
    echo "❌ Policy validation failed - commit rejected"
    exit 1
}

echo "✅ Validation passed"
```

**Acceptance Criteria**:
- ✅ CI fails if registry invalid
- ✅ CI fails if policy references unknown capabilities
- ✅ Pre-commit hook prevents invalid commits
- ✅ Registry report generated on every PR

---

## Architecture & Design

### Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Capability Registry                       │
│                  (config/capabilities/)                      │
│                                                              │
│  ┌────────────────┐  ┌──────────────┐  ┌─────────────┐    │
│  │  index.yaml    │  │ workday/     │  │   hr/       │    │
│  │  (main)        │  │ - hcm.yaml   │  │ - flows.yaml│    │
│  │                │  │ - time.yaml  │  │             │    │
│  │ 13 capabilities│  │ - payroll.ym │  │             │    │
│  └────────────────┘  └──────────────┘  └─────────────┘    │
└────────────┬────────────────────────────────────────────────┘
             │
             │ Loaded at startup
             ↓
┌────────────────────────────────────────────────────────┐
│        CapabilityRegistryService                        │
│  (src/domain/services/capability_registry.py)          │
│                                                         │
│  Methods:                                              │
│  - exists(capability_id) → bool                        │
│  - get(capability_id) → CapabilityEntry               │
│  - matches_wildcard(pattern) → Set[str]               │
│  - validate_capability_list(caps) → List[error]       │
│  - get_by_domain/type/tag() → List[CapabilityEntry]  │
└────────┬───────────────────────────────────────────────┘
         │
         │ Used by:
         │
         ├──→ PolicyLoader (validates references)
         ├──→ ActionService (validates requests)
         ├──→ MCP Server (future: auto-generate tools)
         └──→ CLI Tools (inspection, validation)
```

### Data Flow: Policy Validation

```
┌─────────────────┐
│ Server Startup  │
└────────┬────────┘
         │
         ↓
┌────────────────────────────────────────┐
│ AppSettings (config_validator.py)     │
│ - Validates CAPABILITY_REGISTRY_PATH   │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│ CapabilityRegistryService              │
│ - Loads index.yaml                     │
│ - Builds capability_map (O(1) lookup)  │
└────────┬───────────────────────────────┘
         │
         ↓
┌────────────────────────────────────────┐
│ PolicyLoader                           │
│ - Loads policy-workday.yaml            │
│ - Calls registry.validate_capability_  │
│   list() for each policy rule          │
└────────┬───────────────────────────────┘
         │
         ├──→ ✅ All capabilities valid
         │      → Server starts
         │
         └──→ ❌ Unknown capability found
                → ValueError raised
                → Server fails to start
```

### Performance Considerations

**Startup Time**:
- Registry load: ~5ms (YAML parsing + validation)
- Policy validation: ~10ms (iterate 8 policies × 3 capabilities avg)
- **Total overhead: <20ms** (negligible)

**Runtime Performance**:
- Registry loaded once at startup (singleton pattern)
- All lookups are O(1) via `capability_map` dict
- No disk I/O after startup
- **Zero runtime overhead**

**Memory Footprint**:
- 13 capabilities × ~500 bytes each = ~6.5 KB
- Negligible compared to application memory

---

## Migration Plan

### Phase 1: Create Registry Files (Week 1, Day 1-2)

**Tasks**:
1. Create `config/capabilities/` directory
2. Write `index.yaml` with all 13 capabilities
3. Validate YAML against Pydantic schema
4. Add to version control

**Deliverable**: Complete capability registry file

---

### Phase 2: Implement Registry Service (Week 1, Day 3-4)

**Tasks**:
1. Create `src/domain/entities/capability.py` (Pydantic models)
2. Implement `CapabilityRegistryService` (loader + queries)
3. Write unit tests (15 test cases)
4. Add to dependency injection

**Deliverable**: Working registry service with tests

---

### Phase 3: Policy Validation Integration (Week 1, Day 5)

**Tasks**:
1. Update `PolicyLoader` to validate capabilities
2. Update `AppSettings` to load registry
3. Test startup failure scenarios
4. Update documentation

**Deliverable**: Server fails on invalid policy

---

### Phase 4: Runtime Integration (Week 2, Day 1-2)

**Tasks**:
1. Update `ActionService._validate_capability()`
2. Remove hardcoded `KNOWN_CAPABILITIES` dict
3. Test runtime validation
4. Update error messages

**Deliverable**: Runtime uses registry for validation

---

### Phase 5: CLI Tools & CI (Week 2, Day 3-4)

**Tasks**:
1. Implement `scripts/capability-registry` CLI
2. Add CI workflow for validation
3. Add pre-commit hook
4. Write developer documentation

**Deliverable**: Full tooling ecosystem

---

### Phase 6: Documentation & Training (Week 2, Day 5)

**Tasks**:
1. Write `docs/CAPABILITY_REGISTRY.md` guide
2. Update `README.md` with registry usage
3. Train team on adding new capabilities
4. Record demo video

**Deliverable**: Team ready to use registry

---

## Testing Strategy

### Unit Tests (`tests/unit/domain/test_capability_registry.py`)

```python
class TestCapabilityRegistry:
    def test_load_registry(self):
        """Registry loads successfully from YAML."""
        registry = CapabilityRegistryService("config/capabilities/index.yaml")
        assert len(registry.get_all()) == 13
    
    def test_exists_valid_capability(self):
        """exists() returns True for valid capabilities."""
        registry = CapabilityRegistryService()
        assert registry.exists("workday.hcm.get_employee") is True
    
    def test_exists_invalid_capability(self):
        """exists() returns False for invalid capabilities."""
        registry = CapabilityRegistryService()
        assert registry.exists("workday.hcm.get_salary") is False
    
    def test_wildcard_matching(self):
        """Wildcard patterns expand correctly."""
        registry = CapabilityRegistryService()
        matches = registry.matches_wildcard("workday.hcm.*")
        assert "workday.hcm.get_employee" in matches
        assert "workday.time.get_balance" not in matches
    
    def test_validate_capability_list_valid(self):
        """validate_capability_list() accepts valid capabilities."""
        registry = CapabilityRegistryService()
        errors = registry.validate_capability_list([
            "workday.hcm.get_employee",
            "workday.time.*"
        ])
        assert errors == []
    
    def test_validate_capability_list_invalid(self):
        """validate_capability_list() detects typos."""
        registry = CapabilityRegistryService()
        errors = registry.validate_capability_list([
            "workday.hcm.get_employe"  # Typo
        ])
        assert len(errors) > 0
        assert "get_employe" in errors[0]
        assert "get_employee" in errors[1]  # Suggestion
    
    def test_get_by_domain(self):
        """get_by_domain() filters correctly."""
        registry = CapabilityRegistryService()
        hcm_caps = registry.get_by_domain("workday.hcm")
        assert len(hcm_caps) == 5
    
    def test_get_mfa_required(self):
        """get_mfa_required() returns only MFA capabilities."""
        registry = CapabilityRegistryService()
        mfa_caps = registry.get_mfa_required()
        assert len(mfa_caps) == 3  # Payroll capabilities
        assert all(c.requires_mfa for c in mfa_caps)
```

---

### Integration Tests (`tests/integration/test_registry_policy_integration.py`)

```python
class TestRegistryPolicyIntegration:
    def test_valid_policy_loads(self):
        """Policy with valid capabilities loads successfully."""
        loader = FilePolicyLoaderAdapter("config/policy-workday.yaml")
        policy = loader.load_policy()
        assert len(policy.policies) > 0
    
    def test_invalid_policy_fails_at_startup(self):
        """Policy with typos fails at load time."""
        # Create temp policy with typo
        invalid_policy = """
version: "1.0"
policies:
  - name: "test"
    principal: {type: HUMAN}
    capabilities: ["workday.hcm.get_employe"]
    environments: ["local"]
    effect: "ALLOW"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
            f.write(invalid_policy)
            f.flush()
            
            with pytest.raises(ValueError) as exc:
                FilePolicyLoaderAdapter(f.name).load_policy()
            
            assert "get_employe" in str(exc.value)
            assert "get_employee" in str(exc.value)
    
    def test_wildcard_policy_validation(self):
        """Wildcard patterns in policy are validated."""
        invalid_policy = """
version: "1.0"
policies:
  - name: "test"
    principal: {type: HUMAN}
    capabilities: ["nonexistent.*"]
    environments: ["local"]
    effect: "ALLOW"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml') as f:
            f.write(invalid_policy)
            f.flush()
            
            with pytest.raises(ValueError) as exc:
                FilePolicyLoaderAdapter(f.name).load_policy()
            
            assert "nonexistent.*" in str(exc.value)
```

---

### End-to-End Tests (`tests/e2e/test_capability_validation_e2e.py`)

```python
class TestCapabilityValidationE2E:
    def test_server_starts_with_valid_registry(self):
        """Server starts successfully with valid registry."""
        # This test runs in CI with real config files
        from src.lib.config_validator import settings
        assert settings.CAPABILITY_REGISTRY_PATH.exists()
    
    def test_runtime_validation_uses_registry(self, client):
        """API returns 400 for unknown capabilities (not 403)."""
        token = get_test_token("admin")
        response = client.post(
            "/actions/workday.hcm/nonexistent_action",
            headers={"Authorization": f"Bearer {token}"},
            json={"parameters": {}}
        )
        assert response.status_code == 400
        assert "Unknown capability" in response.json()["message"]
```

---

## Documentation

### Developer Guide: Adding New Capabilities

**File**: `docs/ADDING_CAPABILITIES.md`

```markdown
# Adding New Capabilities to the HR AI Platform

## Overview
When adding a new capability (e.g., a new HR action or workflow), you must update the capability registry **first**. This ensures the capability is validated at startup and discoverable by all components.

## Step-by-Step Guide

### 1. Add to Capability Registry

Edit `config/capabilities/index.yaml`:

\`\`\`yaml
capabilities:
  # ... existing capabilities ...
  
  - id: "workday.hcm.update_emergency_contact"
    name: "Update Emergency Contact"
    domain: "workday.hcm"
    type: "action"
    sensitivity: "high"
    requires_mfa: false
    tags: ["write", "hcm", "pii", "self-service"]
    description: "Allow employees to update their emergency contact information"
\`\`\`

**Fields**:
- `id`: Unique identifier (format: `domain.subdomain.action`)
- `name`: Human-readable name (shown in Backstage)
- `type`: `action` (sync) or `flow` (async workflow)
- `sensitivity`: `low`, `medium`, `high`, or `critical`
- `requires_mfa`: `true` if MFA is required
- `tags`: Classification labels (used for filtering)

### 2. Validate Registry

\`\`\`bash
./scripts/capability-registry validate
\`\`\`

Expected output:
\`\`\`
✅ Registry is valid
   Version: 1.0
   Capabilities: 14
   Domains: 4
\`\`\`

### 3. Add to Policy

Edit `config/policy-workday.yaml`:

\`\`\`yaml
policies:
  - name: "employee-self-service"
    principal:
      type: HUMAN
      okta_group: "employees"
    capabilities:
      - "workday.hcm.get_employee"
      - "workday.hcm.update_contact_info"
      - "workday.hcm.update_emergency_contact"  # NEW
    environments: ["local", "dev", "prod"]
    effect: "ALLOW"
\`\`\`

### 4. Validate Policy Against Registry

\`\`\`bash
./scripts/capability-registry check-policy config/policy-workday.yaml
\`\`\`

### 5. Implement Backend Logic

Add method to appropriate service (e.g., `src/adapters/workday/services/hcm.py`):

\`\`\`python
async def update_emergency_contact(self, params: Dict[str, Any]) -> Dict[str, Any]:
    employee_id = params.get("employee_id")
    contact = params.get("contact")
    
    # ... implementation ...
    
    return {"status": "updated", "employee_id": employee_id}
\`\`\`

### 6. Add MCP Tool (if needed)

Edit `src/mcp/server.py`:

\`\`\`python
@mcp.tool()
async def update_emergency_contact(
    ctx: Context,
    employee_id: str,
    name: str,
    relationship: str,
    phone: str
) -> str:
    """Update employee emergency contact information."""
    return await hcm.update_emergency_contact(ctx, employee_id, {
        "name": name,
        "relationship": relationship,
        "phone": phone
    })
\`\`\`

### 7. Test End-to-End

\`\`\`bash
# Start server
uvicorn src.main:app --reload

# Test via API
curl -X POST http://localhost:8000/actions/workday.hcm/update_emergency_contact \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "employee_id": "EMP001",
      "contact": {
        "name": "Jane Doe",
        "relationship": "Spouse",
        "phone": "+1-555-0199"
      }
    }
  }'
\`\`\`

### 8. Commit Changes

\`\`\`bash
git add config/capabilities/index.yaml
git add config/policy-workday.yaml
git add src/adapters/workday/services/hcm.py
git add src/mcp/server.py
git commit -m "feat: Add update_emergency_contact capability"
\`\`\`

The pre-commit hook will validate your changes automatically.

## Common Mistakes

❌ **Don't add to policy before registry**
- Result: Server fails to start with validation error

❌ **Don't forget to update MCP server**
- Result: Capability works via API but not via MCP

❌ **Don't use inconsistent IDs**
- Wrong: Registry uses `update_contact`, policy uses `update_contact_info`
- Result: Validation error

## Getting Help

Run `./scripts/capability-registry --help` for CLI documentation.
\`\`\`

---

## Metrics & Success Criteria

### Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Policy Typo Detection** | 100% | All typos caught at startup (not runtime) |
| **Startup Time Impact** | <50ms | Registry load + validation overhead |
| **Runtime Performance** | 0ms | No registry lookups after startup |
| **Developer Onboarding** | <30min | New dev can add capability following guide |
| **CI Validation Coverage** | 100% | All PRs touching registry/policy validated |

### Acceptance Criteria

**Must Have** (Blocking for Demo):
- ✅ Registry contains all 13 existing capabilities
- ✅ Server fails to start if policy references unknown capabilities
- ✅ CLI tool can validate registry and policy
- ✅ CI pipeline validates on every PR
- ✅ Documentation explains adding new capabilities

**Should Have** (Post-Demo):
- ✅ Registry includes descriptions for all capabilities
- ✅ Wildcard validation suggests corrections for typos
- ✅ Statistics dashboard shows registry metrics

**Nice to Have** (Future):
- ⏳ Auto-generate MCP tools from registry (Phase 2)
- ⏳ REST API for capability discovery (Phase 2)
- ⏳ Backstage.io integration (Phase 3)

---

## Risks & Mitigation

### Risk 1: Registry Out of Sync with Implementation

**Scenario**: Developer adds new backend method but forgets to update registry.

**Impact**: Capability exists but not discoverable, policy validation fails.

**Mitigation**:
1. Pre-commit hook validates registry
2. CI checks for orphaned implementations (methods not in registry)
3. Developer guide emphasizes "registry first" approach

### Risk 2: Performance Regression

**Scenario**: Registry lookups slow down request handling.

**Impact**: API latency increases.

**Mitigation**:
1. Load registry once at startup (singleton pattern)
2. Use dict for O(1) lookups
3. Add performance tests to CI
4. Monitor P95 latency in production

### Risk 3: Breaking Changes to Registry Schema

**Scenario**: Future requirements force schema changes.

**Impact**: Existing registry files become invalid.

**Mitigation**:
1. Version registry schema (`version: "1.0"`)
2. Support multiple versions during transition
3. Provide migration scripts
4. Document schema changes in CHANGELOG

---

## Future Enhancements (Phase 2+)

### Phase 2: Auto-Generation

**Goal**: Generate MCP tools and API routes from registry.

**Implementation**:
```python
# src/mcp/server_generator.py
def generate_mcp_tools(registry: CapabilityRegistry):
    """Auto-generate MCP tools from capability registry."""
    for capability in registry.get_by_type("action"):
        @mcp.tool(name=capability.id)
        async def dynamic_tool(ctx: Context, **params):
            # Validate params against capability schema
            # Call backend
            # Return result
```

**Benefits**:
- Zero manual MCP tool coding
- Guaranteed consistency between registry and tools
- Automatic parameter validation

---

### Phase 3: Composite Capabilities

**Goal**: Support multi-step workflows in registry.

**Registry Entry**:
```yaml
- id: "hr.onboarding.prepare_workspace"
  type: "composite"
  requires_capabilities:
    - "workday.hcm.get_employee"
    - "slack.create_channel"
    - "google.provision_account"
  flow_diagram: |
    graph TD
      A[Get employee] --> B[Create channel]
      B --> C[Provision account]
```

**Benefits**:
- Visual workflow documentation
- Dependency tracking
- Auto-generate orchestration code

---

### Phase 4: REST API

**Goal**: Expose registry via HTTP API.

**Endpoints**:
```
GET /catalog/capabilities
GET /catalog/capabilities/{capability_id}
GET /catalog/capabilities/available  # RBAC-aware
GET /catalog/schemas/{schema_name}
```

**Benefits**:
- Dynamic MCP tool discovery
- Backstage.io integration
- Third-party integrations

---

## Appendix

### Complete Registry Example

See `config/capabilities/index.yaml` in FR-001.

### CLI Reference

```
Usage: capability-registry [OPTIONS] COMMAND

Commands:
  list           List capabilities with filtering
  validate       Validate registry structure
  check-policy   Validate policy against registry
  deps           Show capability dependencies
  stats          Show registry statistics

Options:
  --registry PATH    Path to capability registry [default: config/capabilities/index.yaml]
  --help            Show this message and exit
```

### Policy Validation Error Examples

```
Policy 'employee-self-service':
  Unknown capability: 'workday.hcm.get_employe'
    Did you mean: workday.hcm.get_employee

Policy 'admin-all-access':
  Wildcard pattern 'calendar.*' matches no capabilities

Capability group 'payroll_actions':
  Unknown capability: 'workday.payroll.update_salary'
    Did you mean: workday.payroll.get_compensation
```

---

**End of PRD**