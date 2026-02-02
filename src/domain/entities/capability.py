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
    id: str = Field(description="Unique capability identifier (e.g., workday.hcm.get_employee)")
    name: str = Field(description="Human-readable name")
    domain: str = Field(description="Domain/subdomain (e.g., workday.hcm)")
    type: CapabilityType = Field(description="Capability type (action or flow)")
    sensitivity: SensitivityLevel = Field(description="Data sensitivity level")
    requires_mfa: bool = Field(default=False, description="Whether MFA is required")
    tags: List[str] = Field(default=[], description="Classification tags")
    description: Optional[str] = Field(None, description="Detailed description")
    deprecated: bool = Field(default=False, description="Whether capability is deprecated")
    implementation_flow: Optional[str] = Field(None, description="Mermaid diagram for composite capabilities")
    requires_capabilities: List[str] = Field(default=[], description="Required capabilities for composite ones")

class CapabilityRegistryMetadata(BaseModel):
    last_updated: str
    owner: str
    description: str

class CapabilityRegistry(BaseModel):
    version: str
    metadata: CapabilityRegistryMetadata
    capabilities: List[CapabilityEntry]
