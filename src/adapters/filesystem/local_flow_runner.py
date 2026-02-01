import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from src.domain.ports.flow_runner import FlowRunnerPort

class LocalFlowRunnerAdapter(FlowRunnerPort):
    def __init__(self):
        # In-memory store for MVP. For persistence, this should write to a file/DB.
        self._executions: Dict[str, Dict[str, Any]] = {}

    async def start_flow(
        self,
        domain: str,
        flow: str,
        params: Dict[str, Any],
        principal_id: str,
    ) -> str:
        flow_id = str(uuid.uuid4())
        self._executions[flow_id] = {
            "flow_id": flow_id,
            "domain": domain,
            "flow": flow,
            "status": "RUNNING",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "current_step": "init",
            "params": params,
            "principal_id": principal_id,
            "result": None,
            "error": None
        }
        return flow_id

    async def get_flow_status(self, flow_id: str) -> Optional[Dict[str, Any]]:
        return self._executions.get(flow_id)
