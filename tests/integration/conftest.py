import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.api.dependencies import get_policy_engine
from src.domain.services.policy_engine import PolicyEngine

@pytest_asyncio.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_policy_engine(mocker):
    """
    Shared mock policy engine for integration tests.
    When used, it automatically overrides the get_policy_engine dependency.
    """
    from src.domain.services.policy_engine import PolicyEvaluationResult, PolicyEngine
    from src.api.dependencies import get_policy_engine
    
    mock = mocker.Mock(spec=PolicyEngine)
    # Default return value to satisfy Pydantic validation in SecurityContext
    mock.evaluate.return_value = PolicyEvaluationResult(
        allowed=True,
        policy_name="mock-allow-all",
        audit_level="BASIC"
    )
    
    # Apply override
    app.dependency_overrides[get_policy_engine] = lambda: mock
    yield mock
    # Clean up override
    if get_policy_engine in app.dependency_overrides:
        del app.dependency_overrides[get_policy_engine]
