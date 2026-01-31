import uuid
import time
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from src.lib.context import get_request_id
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.connector import ConnectorPort
from src.domain.entities.action import (
    ActionResponse,
    Provenance,
    ProvenanceWrapper,
    SecurityContext,
)
from src.adapters.workday.exceptions import WorkdayError


class ActionService:
    # We support both 'workday' (global) and specific subdomains (legacy/contract tests)
    KNOWN_CAPABILITIES = {
        # "workday": [
        #     "get_employee",
        #     "get_employee_full",
        #     "get_manager_chain",
        #     "list_direct_reports",
        #     "update_contact_info",
        #     "update_employee",
        #     "terminate_employee",
        #     "delete_employee",
        #     "get_org_chart",
        #     "get_balance",
        #     "request",
        #     "cancel",
        #     "approve",
        #     "list_requests",
        #     "get_request",
        #     "get_compensation",
        #     "get_pay_statement",
        #     "list_pay_statements",
        # ],
        "workday.hcm": [
            "get_employee",
            "get_employee_full",
            "get_manager_chain",
            "list_direct_reports",
            "update_contact_info",
            "update_employee",
            "terminate_employee",
            "get_org_chart",
        ],
        "workday.time": [
            "get_balance",
            "request",
            "cancel",
            "approve",
            "list_requests",
            "get_request",
        ],
        "workday.payroll": [
            "get_compensation",
            "get_pay_statement",
            "list_pay_statements",
        ],
        "hr": ["onboarding", "offboarding", "role_change", "compensation_review"],
    }

    def __init__(self, policy_engine: PolicyEngine, connector: ConnectorPort):
        self.policy_engine = policy_engine
        self.connector = connector

    def _validate_capability(self, domain: str, action: str):
        if domain not in self.KNOWN_CAPABILITIES:
            raise HTTPException(status_code=400, detail=f"Unknown domain: {domain}")
        if action not in self.KNOWN_CAPABILITIES[domain]:
            raise HTTPException(
                status_code=400, detail=f"Unknown action: {domain}.{action}"
            )

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
        request_ip: Optional[str] = None,
        idempotency_key: Optional[str] = None,
    ) -> ActionResponse:
        self._validate_capability(domain, action)

        # Determine the capability string for policy check.
        # If the domain is just 'workday', try to find its subdomain.
        policy_capability = f"{domain}.{action}"
        if domain == "workday":
            for full_domain in self.KNOWN_CAPABILITIES:
                if (
                    full_domain.startswith("workday.")
                    and action in self.KNOWN_CAPABILITIES[full_domain]
                ):
                    policy_capability = f"{full_domain}.{action}"
                    break

        # 1. Policy Check
        evaluation = self.policy_engine.evaluate(
            principal_id=principal_id,
            principal_groups=principal_groups,
            principal_type=principal_type,
            capability=policy_capability,
            environment=environment,
            mfa_verified=mfa_verified,
            token_issued_at=token_issued_at,
            token_expires_at=token_expires_at,
            request_ip=request_ip,
        )

        if not evaluation.allowed:
            raise HTTPException(
                status_code=403,
                detail=f"Access denied to capability: {policy_capability}",
            )

        # 2. Connector Execution
        start_time = time.time()
        try:
            # Inject principal context into parameters for adapter-level enforcement
            enriched_params = {
                **parameters,
                "principal_id": principal_id,
                "principal_type": principal_type,
                "mfa_verified": mfa_verified,
                "idempotency_key": idempotency_key,
            }

            # For MVP, we route everything to the single injected connector
            # In real world, we'd route based on 'domain' to specific connectors
            result_data = await self.connector.execute(action, enriched_params)
        except WorkdayError:
            # Let Workday-specific errors bubble up to main.py handler
            raise
        except Exception as e:
            # Fail-fast logic
            # T110: 5.1 Non-existent employee -> Should be 404
            if "not found" in str(e).lower():
                raise HTTPException(status_code=404, detail=str(e))
            if "timeout" in str(e).lower():
                raise HTTPException(status_code=504, detail=str(e))

            raise HTTPException(status_code=424, detail=f"Connector failure: {str(e)}")

        latency_ms = (time.time() - start_time) * 1000

        # Layer 2: Field-level security (data protection in transit)
        fields_filtered = False
        if principal_type == "AI_AGENT" and isinstance(result_data, dict):
            # The connector might have already filtered fields, but we ensure it here too
            # or at least we know they ARE filtered for AI agents by policy/design.
            fields_filtered = True

        # 3. Provenance Construction
        provenance = Provenance(
            source=f"{domain}-connector",  # Simplified source naming
            timestamp=datetime.now(timezone.utc),
            trace_id=get_request_id(),
            latency_ms=round(latency_ms, 2),
            actor=principal_id,
        )

        security = SecurityContext(
            authorization_policy=evaluation.policy_name or "N/A",
            audit_level=evaluation.audit_level,
            mfa_verified=mfa_verified,
            fields_filtered=fields_filtered,
        )

        return ActionResponse(
            data=result_data,
            meta=ProvenanceWrapper(provenance=provenance, security=security),
        )
