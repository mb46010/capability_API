from __future__ import annotations
from enum import Enum
from typing import List, Dict, Optional, Union, Any
from pydantic import BaseModel, Field

class PrincipalType(str, Enum):
    HUMAN = "HUMAN"
    MACHINE = "MACHINE"
    AI_AGENT = "AI_AGENT"

class Environment(str, Enum):
    LOCAL = "local"
    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"

class AuditLevel(str, Enum):
    BASIC = "BASIC"
    VERBOSE = "VERBOSE"

class PolicyMetadata(BaseModel):
    last_reviewed: Optional[str] = Field(None, description="Date of the last security review for this policy")
    reviewed_by: Optional[str] = Field(None, description="Identity of the reviewer")
    ticket: Optional[str] = Field(None, description="Reference to the Jira or ServiceNow ticket for the review")

class PrincipalDefinition(BaseModel):
    type: PrincipalType = Field(description="The type of principal (HUMAN, MACHINE, AI_AGENT)")
    okta_subject: Optional[str] = Field(None, description="The unique subject ID from Okta (e.g., email or service name)")
    okta_group: Optional[str] = Field(None, description="Okta group name for group-based access")
    description: Optional[str] = Field(None, description="Human-readable description of what this principal represents")
    provisioning_ticket: Optional[str] = Field(None, description="Audit reference for principal creation")

class PolicyConditions(BaseModel):
    max_ttl_seconds: Optional[int] = Field(None, ge=60, description="Maximum allowed token lifetime in seconds")
    require_mfa: Optional[bool] = Field(None, description="If true, requires Multi-Factor Authentication presence in token")
    ip_allowlist: Optional[List[str]] = Field(None, description="Allowed source IP addresses or ranges")
    time_window: Optional[Dict[str, str]] = Field(None, description="Operational window (e.g., start: '09:00', end: '17:00')")
    required_scope: Optional[str] = Field(None, description="Scope required to access this capability (e.g., 'mcp:use')")
    max_auth_age_seconds: Optional[int] = Field(None, description="Maximum allowed age of authentication in seconds")

class PolicyRule(BaseModel):
    name: str = Field(description="Unique, descriptive name for the rule")
    description: Optional[str] = Field(None, description="Context on why this access is granted")
    principal: Union[str, PrincipalDefinition] = Field(description="A reference to a principal ID or an inline definition")
    capabilities: Union[List[str], str] = Field(description="List of capability strings or a capability group reference")
    environments: List[Environment] = Field(description="Deployment environments where this rule applies")
    effect: str = Field(default="ALLOW", description="The effect of matching this rule (currently only ALLOW)")
    conditions: Optional[PolicyConditions] = Field(None, description="Dynamic constraints that must be satisfied for the rule to apply")
    audit: AuditLevel = Field(default=AuditLevel.BASIC, description="The level of audit detail to capture (BASIC or VERBOSE)")
    approval: Optional[Dict[str, Any]] = Field(None, description="Audit record of who approved this specific grant")

class AccessPolicy(BaseModel):
    version: str = Field(description="The schema version of the policy document")
    metadata: Optional[PolicyMetadata] = Field(None, description="High-level audit and review metadata")
    principals: Optional[Dict[str, PrincipalDefinition]] = Field(default={}, description="Registry of known principals and their bindings")
    capability_groups: Optional[Dict[str, List[str]]] = Field(default={}, description="Named sets of related capabilities for easier reuse")
    policies: List[PolicyRule] = Field(description="The ordered list of rules to evaluate")
    connector_constraints: Optional[Dict[str, Any]] = Field(None, description="Default limits and timeouts for external connectors")

    def validate_references(self) -> List[str]:
        errors = []
        policy_names = set()
        
        for rule in self.policies:
            # Check for duplicate policy names
            if rule.name in policy_names:
                errors.append(f"Duplicate policy name found: '{rule.name}'")
            policy_names.add(rule.name)

            # Check for undefined principals
            if isinstance(rule.principal, str):
                if rule.principal not in self.principals:
                    errors.append(f"Policy '{rule.name}' references undefined principal '{rule.principal}'")
            
            # Check for undefined capability groups
            if isinstance(rule.capabilities, str):
                if rule.capabilities not in self.capability_groups:
                    errors.append(f"Policy '{rule.name}' references undefined capability group '{rule.capabilities}'")

            # Check for ambiguous inline principals (Guardrail)
            if isinstance(rule.principal, PrincipalDefinition):
                p = rule.principal
                has_binding = p.okta_subject or p.okta_group
                if has_binding and p.type:
                    # Not an error, but flag it — this policy will ONLY match
                    # on the specific binding, never as a generic type match
                    errors.append(
                        f"WARNING: Policy '{rule.name}' has inline principal with both "
                        f"type '{p.type.value}' and a specific binding. "
                        f"It will only match on the binding, not on type alone."
                    )
        
        return errors