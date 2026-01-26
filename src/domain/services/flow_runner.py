from typing import Dict, Any
from src.domain.ports.flow_runner import FlowRunnerPort
from src.domain.entities.flow import FlowStatusResponse

class FlowRunner:
    def __init__(self, adapter: FlowRunnerPort):
        self.adapter = adapter

    async def start_flow(self, domain: str, flow: str, params: Dict[str, Any]) -> str:
        # Here we could add logic to validate if the flow exists in a registry
        # For now, pass through
        return await self.adapter.start_flow(domain, flow, params)

    async def get_status(self, flow_id: str) -> FlowStatusResponse:
        raw_status = await self.adapter.get_flow_status(flow_id)
        if not raw_status:
             raise ValueError(f"Flow {flow_id} not found")
        
        # Convert raw dict to Pydantic model
        return FlowStatusResponse(
            flow_id=raw_status["flow_id"],
            status=raw_status["status"],
            start_time=raw_status.get("start_time"),
            current_step=raw_status.get("current_step"),
            result=raw_status.get("result"),
            error=raw_status.get("error")
        )
