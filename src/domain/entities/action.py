from typing import Dict, Any, List, Union
from datetime import datetime
from pydantic import BaseModel

class ActionRequest(BaseModel):
    parameters: Dict[str, Any]
    dry_run: bool = False

class Provenance(BaseModel):
    source: str
    timestamp: datetime
    trace_id: str
    latency_ms: float
    actor: str

class ProvenanceWrapper(BaseModel):
    provenance: Provenance

class ActionResponse(BaseModel):
    data: Union[Dict[str, Any], List[Any]]
    meta: ProvenanceWrapper
