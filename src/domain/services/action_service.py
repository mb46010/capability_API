import uuid
import time
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.connector import ConnectorPort
from src.domain.entities.action import ActionResponse, Provenance, ProvenanceWrapper

class ActionService:
    def __init__(self, policy_engine: PolicyEngine, connector: ConnectorPort):
        self.policy_engine = policy_engine
        self.connector = connector

    async def execute_action(
        self,
        domain: str,
        action: str,
        parameters: dict,
        principal_id: str,
        principal_groups: list,
        principal_type: str,
        environment: str,
        # New context for policy conditions
        mfa_verified: bool = False,
        token_issued_at: Optional[int] = None,
        token_expires_at: Optional[int] = None,
        request_ip: Optional[str] = None
    ) -> ActionResponse:
        capability = f"{domain}.{action}"
        
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
            raise HTTPException(status_code=403, detail=f"Access denied to capability: {capability}")

        # 2. Connector Execution
        start_time = time.time()
        try:
            # For MVP, we route everything to the single injected connector
            # In real world, we'd route based on 'domain' to specific connectors
            result_data = await self.connector.execute(action, parameters)
        except Exception as e:
            # Fail-fast logic
            raise HTTPException(status_code=424, detail=f"Connector failure: {str(e)}")
        
        latency_ms = (time.time() - start_time) * 1000

        # 3. Provenance Construction
        provenance = Provenance(
            source=f"{domain}-connector", # Simplified source naming
            timestamp=datetime.now(timezone.utc),
            trace_id=str(uuid.uuid4()),
            latency_ms=round(latency_ms, 2),
            actor=principal_id
        )

        return ActionResponse(
            data=result_data,
            meta=ProvenanceWrapper(provenance=provenance)
        )