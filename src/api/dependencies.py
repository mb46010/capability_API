import os
from pathlib import Path
from functools import lru_cache
from fastapi import Depends
from src.adapters.auth import MockOktaProvider, MockTokenVerifier, create_auth_dependency
from src.domain.services.policy_engine import PolicyEngine
from src.adapters.filesystem.policy_loader import FilePolicyLoaderAdapter
from src.domain.ports.connector import ConnectorPort
from src.domain.ports.flow_runner import FlowRunnerPort
from src.adapters.filesystem.local_flow_runner import LocalFlowRunnerAdapter
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig

# Auth Dependencies
provider = MockOktaProvider()
verifier = MockTokenVerifier(provider)
get_current_principal = create_auth_dependency(verifier)

# Policy Engine Dependency
# Updated to point to workday-specific policy for US2 verification
POLICY_PATH = os.getenv("POLICY_PATH", "config/policy-workday.yaml")
if not Path(POLICY_PATH).exists():
    raise FileNotFoundError(f"Policy file not found: {POLICY_PATH}")

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
