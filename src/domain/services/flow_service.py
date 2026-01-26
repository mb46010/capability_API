from typing import Dict, Any, List, Optional
from fastapi import HTTPException
from src.domain.ports.flow_runner import FlowRunnerPort
from src.domain.services.policy_engine import PolicyEngine
from src.domain.entities.flow import FlowStatusResponse

class FlowService:
    def __init__(self, policy_engine: PolicyEngine, adapter: FlowRunnerPort):
        self.policy_engine = policy_engine
        self.adapter = adapter

    async def start_flow(
        self,
        domain: str,
        flow: str,
        params: Dict[str, Any],
        principal_id: str,
        principal_groups: List[str],
        principal_type: str,
        environment: str,
        # Context for conditions
        mfa_verified: bool = False,
        token_issued_at: Optional[int] = None,
        token_expires_at: Optional[int] = None,
        request_ip: Optional[str] = None
    ) -> str:
        capability = f"{domain}.{flow}"

        # 1. Policy Check
        evaluation = self.policy_engine.evaluate(
            principal_id=principal_id,
            principal_groups=principal_groups,
            principal_type=principal_type,
            capability=capability,
            environment=environment,
            mfa_verified=mfa_verified,
            token_issued_at=token_issued_at,
            token_expires_at=token_expires_at,
            request_ip=request_ip
        )

        if not evaluation.allowed:
            raise HTTPException(status_code=403, detail=f"Access denied to flow: {capability}")

        # 2. Start Flow via Adapter
        return await self.adapter.start_flow(domain, flow, params)

    async def get_status(self, flow_id: str) -> FlowStatusResponse:
        # Note: In a real system, we might want to check if the principal has access to view this flow status.
        # For now, we'll assume getting status is allowed if authenticated (or add specific policy check if needed).
        # The prompt specifically mentioned "trigger any flow", implying start_flow is the critical gap.
        
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
