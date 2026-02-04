import pytest
import os
import shutil

# Set dummy secret for tests before importing modules that trigger settings initialization
if "MOCK_OKTA_TEST_SECRET" not in os.environ:
    os.environ["MOCK_OKTA_TEST_SECRET"] = "test-secret-only-for-pytest"

from src.adapters.filesystem.logger import JSONLLogger
from src.adapters.workday.client import WorkdaySimulator
from src.api.dependencies import provider

@pytest.fixture
def test_logger(tmp_path):
    """
    Fixture providing a JSONLLogger instance pointing to a temporary file.
    """
    log_dir = tmp_path / "logs"
    log_file = log_dir / "audit.jsonl"
    return JSONLLogger(log_path=str(log_file))

@pytest.fixture(scope="session")
def mock_provider():
    """Shared mock Okta provider for token generation."""
    return provider

@pytest.fixture
def simulator():
    """Fresh WorkdaySimulator instance with fixture data."""
    return WorkdaySimulator()

@pytest.fixture
def admin_token(mock_provider):
    """Pre-generated admin token with MFA."""
    return mock_provider.issue_token(
        subject="admin@local.test",
        groups=["hr-platform-admins"],
        additional_claims={"amr": ["mfa", "pwd"]}
    )

@pytest.fixture
def user_token(mock_provider):
    """Pre-generated employee token."""
    return mock_provider.issue_token(
        subject="user@local.test",
        groups=["employees"]
    )

@pytest.fixture
def agent_token(mock_provider):
    """Pre-generated AI agent token with short TTL."""
    return mock_provider.issue_token(
        subject="agent-assistant@local.test",
        principal_type="AI_AGENT",
        ttl_seconds=300
    )

@pytest.fixture
def machine_token(mock_provider):
    """Pre-generated machine token."""
    return mock_provider.issue_token(
        subject="svc-workflow@local.test",
        principal_type="MACHINE"
    )
