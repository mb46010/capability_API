import os
from functools import lru_cache
from fastapi import Depends
from src.adapters.auth import MockOktaProvider, MockTokenVerifier, create_auth_dependency
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.domain.ports.connector import ConnectorPort
from src.adapters.connectors.mock_connector import MockConnectorAdapter
from src.domain.ports.flow_runner import FlowRunnerPort
from src.adapters.filesystem.local_flow_runner import LocalFlowRunnerAdapter

# Auth Dependencies
provider = MockOktaProvider()
verifier = MockTokenVerifier(provider)
get_current_principal = create_auth_dependency(verifier)

# Policy Engine Dependency
POLICY_PATH = os.getenv("POLICY_PATH", "config/policy.yaml")

@lru_cache
def get_policy_engine() -> PolicyEngine:
    loader = FilePolicyLoaderAdapter(POLICY_PATH)
    policy = loader.load_policy()
    return PolicyEngine(policy)

# Connector Dependency
@lru_cache
def get_connector() -> ConnectorPort:
    return MockConnectorAdapter()

# Flow Runner Adapter Dependency
@lru_cache
def get_flow_runner_adapter() -> FlowRunnerPort:
    return LocalFlowRunnerAdapter()
