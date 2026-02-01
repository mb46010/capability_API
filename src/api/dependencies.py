import os
from pathlib import Path
from functools import lru_cache
from fastapi import Depends
from src.adapters.auth import (
    MockOktaProvider,
    create_auth_dependency,
    AuthConfig,
    create_token_verifier,
)
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.domain.ports.connector import ConnectorPort
from src.domain.ports.flow_runner import FlowRunnerPort
from src.adapters.filesystem.local_flow_runner import LocalFlowRunnerAdapter
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig
from src.lib.config_validator import settings

# Auth Dependencies
if settings.ENVIRONMENT == "local":
    provider = MockOktaProvider()
    auth_config = AuthConfig.for_local_development()
    verifier = create_token_verifier(auth_config, mock_provider=provider)
else:
    issuer = os.getenv("OKTA_ISSUER")
    if not issuer:
        raise RuntimeError("OKTA_ISSUER is required when ENVIRONMENT is not local")
    audience = os.getenv("OKTA_AUDIENCE", "api://hr-ai-platform")
    client_id = os.getenv("OKTA_CLIENT_ID")
    auth_config = AuthConfig.for_production(
        issuer=issuer,
        audience=audience,
        client_id=client_id,
    )
    provider = None
    verifier = create_token_verifier(auth_config)

get_current_principal = create_auth_dependency(verifier)

# Policy Engine Dependency
# Updated to point to workday-specific policy for US2 verification
# POLICY_PATH is now validated by settings
POLICY_PATH = settings.POLICY_PATH

@lru_cache
def get_policy_engine() -> PolicyEngine:
    loader = FilePolicyLoaderAdapter(POLICY_PATH)
    policy = loader.load_policy()
    return PolicyEngine(policy)

# Connector Dependency
@lru_cache
def get_connector() -> ConnectorPort:
    # Use WorkdaySimulator with default config
    return WorkdaySimulator()

# Flow Runner Adapter Dependency
@lru_cache
def get_flow_runner_adapter() -> FlowRunnerPort:
    return LocalFlowRunnerAdapter()
