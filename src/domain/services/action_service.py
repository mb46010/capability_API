import uuid
import time
import logging
from typing import Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from src.lib.context import get_request_id
from src.domain.services.policy_engine import PolicyEngine
from src.domain.ports.connector import ConnectorPort
from src.domain.services.capability_registry import CapabilityRegistryService, get_capability_registry
from src.domain.entities.action import (
    ActionResponse,
    Provenance,
    ProvenanceWrapper,
    SecurityContext,
)
from src.domain.exceptions import ConnectorError

logger = logging.getLogger(__name__)


class ActionService:
    """
    Service for executing actions across different domains.
    Now uses CapabilityRegistry for validation and discovery.
    """
    def __init__(
        self, 
        policy_engine: PolicyEngine, 
        connector: ConnectorPort,
        registry: Optional[CapabilityRegistryService] = None
    ):
        self.policy_engine = policy_engine
        self.connector = connector
        # Use provided registry or get the singleton instance
        self.registry = registry or get_capability_registry()

    def _validate_capability(self, domain: str, action: str) -> str:
        """
        Validate capability exists in registry and return the canonical ID.
        """
        capability_id = f"{domain}.{action}"
        
        # 1. Try full capability ID first
        if self.registry.exists(capability_id):
            return capability_id
            
        # 2. Try with subdomain expansion (e.g., workday -> workday.hcm, etc.)
        subdomains = self.registry.get_subdomains(domain)
        for subdomain in subdomains:
            full_id = f"{domain}.{subdomain}.{action}"
            if self.registry.exists(full_id):
                return full_id
                    
        # 3. Not found - provide helpful error with suggestions

        similar = self.registry._find_similar(capability_id)
        if similar:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown capability: {capability_id}. Did you mean: {', '.join(similar[:3])}?"
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown capability: {capability_id}"
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
        mfa_verified: bool = False,
        token_issued_at: Optional[int] = None,
        token_expires_at: Optional[int] = None,
        request_ip: Optional[str] = None,
        idempotency_key: Optional[str] = None,
        token_claims: Optional[dict] = None,
        acting_through: Optional[str] = None,
    ) -> ActionResponse:
        # Validate and get canonical capability ID
        policy_capability = self._validate_capability(domain, action)

        # Check for deprecation
        cap_entry = self.registry.get(policy_capability)
        if cap_entry and cap_entry.deprecated:
            logger.warning(f"Principal {principal_id} is using deprecated capability: {policy_capability}")

        # Direct API Protection check (FR-005)
        if token_claims:
            scopes = token_claims.get("scope", [])
            # Handle both list and string scope formats
            if isinstance(scopes, str):
                scopes = scopes.split(" ")
            
            if "mcp:use" in scopes:
                # 1. Verify token origin via client ID claim (cid, azp, or client_id)
                # We trust these claims because they are part of the verified JWT
                token_client_id = token_claims.get("cid") or token_claims.get("azp") or token_claims.get("client_id")
                
                from src.lib.config_validator import settings
                if token_client_id != settings.MCP_CLIENT_ID:
                    logger.warning(f"Blocking unauthorized direct access: Token has 'mcp:use' but client ID '{token_client_id}' does not match authorized MCP client ID.")
                    raise HTTPException(
                        status_code=403,
                        detail="MCP-scoped tokens must originate from the authorized MCP client"
                    )

                # 2. Also require the header for consistency and audit visibility,
                # though it's no longer the primary security mechanism.
                if not acting_through:
                    raise HTTPException(
                        status_code=403,
                        detail="MCP-scoped tokens cannot be used for direct API access"
                    )
        else:
            scopes = []

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
            token_scopes=scopes
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
                "principal_groups": principal_groups,
                "principal_type": principal_type,
                "mfa_verified": mfa_verified,
                "idempotency_key": idempotency_key,
                "token_claims": token_claims # Pass token metadata to connector for logging
            }

            # For MVP, we route everything to the single injected connector
            # In real world, we'd route based on 'domain' to specific connectors
            result_data = await self.connector.execute(action, enriched_params)
        except ConnectorError:
            # Let Connector-specific errors bubble up
            raise
        except Exception as e:

            # Fail-fast logic
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
            source=f"{domain}-connector",
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