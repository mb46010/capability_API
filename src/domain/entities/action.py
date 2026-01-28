from datetime import datetime
from typing import Dict, Any, List, Union, Optional
from pydantic import BaseModel, Field

class EmployeeReference(BaseModel):
    employee_id: str = Field(description="Unique identifier of the employee")
    display_name: str = Field(description="Full display name of the employee")

class Money(BaseModel):
    amount: float = Field(description="Monetary amount")
    currency: str = Field(description="ISO currency code (e.g. USD)")
    frequency: Optional[str] = Field(default=None, description="Payment frequency (e.g. ANNUAL, HOURLY)")

class ActionRequest(BaseModel):
    parameters: Dict[str, Any] = Field(description="Key-value pairs of parameters for the action")
    dry_run: bool = Field(default=False, description="If true, only validate and simulate the action without making changes")

class Provenance(BaseModel):
    source: str = Field(description="The system or component that generated this data")
    timestamp: datetime = Field(description="ISO-8601 timestamp of when the action was executed")
    trace_id: str = Field(description="Unique identifier for tracing this request across systems")
    latency_ms: float = Field(description="Execution time in milliseconds")
    actor: str = Field(description="The principal ID that performed the action")

class ProvenanceWrapper(BaseModel):
    provenance: Provenance = Field(description="Metadata about the action execution")

class ActionResponse(BaseModel):
    data: Union[Dict[str, Any], List[Any]] = Field(description="The actual result payload of the action")
    meta: ProvenanceWrapper = Field(description="Execution metadata and audit trail")