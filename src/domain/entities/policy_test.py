from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TestCategory(str, Enum):
    POSITIVE = "positive"  # Expected to ALLOW
    NEGATIVE = "negative"  # Expected to DENY
    EDGE_CASE = "edge_case"


class TestPrincipal(BaseModel):
    type: Optional[str] = Field(None, description="Principal type (HUMAN, MACHINE, AI_AGENT)")
    subject: Optional[str] = Field(None, description="Principal subject/ID")
    groups: List[str] = Field(default_factory=list, description="Principal groups")
    mfa_verified: bool = Field(default=False, description="MFA status")
    token_issued_at: Optional[int] = Field(None, description="Token issue timestamp")
    token_expires_at: Optional[int] = Field(None, description="Token expiry timestamp")
    request_ip: Optional[str] = Field(None, description="Request IP address")


class TestRequest(BaseModel):
    capability: str = Field(description="Capability being tested")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Request parameters")
    environment: Optional[str] = Field(None, description="Environment (local, dev, prod)")


class ExpectedResult(BaseModel):
    allowed: bool = Field(description="Expected allow/deny result")
    policy_matched: Optional[str] = Field(None, description="Expected policy name")
    audit_level: Optional[str] = Field(None, description="Expected audit level (BASIC, VERBOSE)")
    reason_contains: Optional[str] = Field(None, description="Expected substring in denial reason")
    environments: Optional[Dict[str, bool]] = Field(
        None, description="Override 'allowed' per environment"
    )


class PolicyTestCase(BaseModel):
    id: str = Field(description="Unique test case ID (e.g., EMP-001)")
    name: str = Field(description="Human-readable test name")
    category: TestCategory = Field(description="Test category")
    principal: Optional[TestPrincipal] = Field(None, description="Simulated principal")
    request: Optional[TestRequest] = Field(None, description="Request details")
    expected: ExpectedResult = Field(description="Expected outcome")
    skip: bool = Field(default=False, description="Skip this test")
    tags: List[str] = Field(default_factory=list, description="Filtering tags")


class PolicyTestMetadata(BaseModel):
    name: str
    owner: str
    description: str
    security_requirement: Optional[str] = None
    last_updated: str


class PolicyTestSuite(BaseModel):
    version: str
    metadata: PolicyTestMetadata
    defaults: Optional[Dict[str, Any]] = Field(
        None, description="Shared attributes for all test cases"
    )
    test_cases: List[PolicyTestCase]