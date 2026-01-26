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
    last_reviewed: Optional[str] = None
    reviewed_by: Optional[str] = None
    ticket: Optional[str] = None

class PrincipalDefinition(BaseModel):
    type: PrincipalType
    okta_subject: Optional[str] = None
    okta_group: Optional[str] = None
    description: Optional[str] = None
    provisioning_ticket: Optional[str] = None

class PolicyConditions(BaseModel):
    max_ttl_seconds: Optional[int] = Field(None, ge=60)
    require_mfa: Optional[bool] = None
    ip_allowlist: Optional[List[str]] = None
    time_window: Optional[Dict[str, str]] = None

class PolicyRule(BaseModel):
    name: str
    description: Optional[str] = None
    principal: Union[str, PrincipalDefinition]
    capabilities: Union[List[str], str]
    environments: List[Environment]
    effect: str = "ALLOW"  # Currently only ALLOW supported
    conditions: Optional[PolicyConditions] = None
    audit: AuditLevel = AuditLevel.BASIC
    approval: Optional[Dict[str, Any]] = None

class AccessPolicy(BaseModel):
    version: str
    metadata: Optional[PolicyMetadata] = None
    principals: Optional[Dict[str, PrincipalDefinition]] = {}
    capability_groups: Optional[Dict[str, List[str]]] = {}
    policies: List[PolicyRule]
    connector_constraints: Optional[Dict[str, Any]] = None
