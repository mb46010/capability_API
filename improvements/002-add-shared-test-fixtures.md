# 002: Consolidate Shared Test Fixtures

## Impact
**Effort**: Low (2-3 hours) | **Impact**: Medium | **Priority**: 2

## Location
- **File(s)**: `tests/conftest.py`, `tests/integration/conftest.py`, various test files
- **Component/Module**: Test Infrastructure

## Current State

Test fixtures are duplicated across multiple test files. Each test module recreates similar fixtures:

```python
# tests/unit/adapters/workday/services/test_service_hcm.py
@pytest.fixture
def simulator():
    return WorkdaySimulator()

# tests/unit/adapters/workday/services/test_service_time.py
@pytest.fixture
def simulator():
    return WorkdaySimulator()

# tests/integration/test_scenarios.py
# Uses provider directly without fixture
token = provider.issue_token(...)
```

The root `conftest.py` only has one fixture (`test_logger`), missing common fixtures used across tests.

## Proposed Improvement

Centralize common fixtures in `conftest.py` at appropriate scopes:
- `provider` - Mock Okta provider for token generation
- `simulator` - Workday simulator with fixture data
- `admin_token` / `user_token` / `agent_token` - Pre-generated tokens for common principals

## Benefits

- **Developer Productivity**: Less boilerplate in new tests
- **Consistency**: Same fixture behavior across all tests
- **Maintainability**: Single place to update fixture configuration
- **Test Speed**: Session-scoped fixtures avoid repeated initialization

**Estimated time savings**: 10-15 minutes per new test file

## Implementation

### Approach
Move common fixtures to root `conftest.py` with appropriate scopes. Use `pytest.fixture(scope="session")` for expensive fixtures.

### Estimated Effort
2-3 hours

### Steps
1. Identify all duplicated fixtures across test files
2. Create shared fixtures in `tests/conftest.py`
3. Update test files to use shared fixtures
4. Remove duplicate fixture definitions
5. Run full test suite to verify

## Example

### Before
```python
# tests/unit/adapters/workday/services/test_service_hcm.py
@pytest.fixture
def simulator():
    return WorkdaySimulator()

@pytest.fixture
def hcm_service(simulator):
    return WorkdayHCMService(simulator)

# Each test file has similar boilerplate...
```

### After
```python
# tests/conftest.py
import pytest
from src.adapters.workday.client import WorkdaySimulator
from src.api.dependencies import provider

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
```

```python
# tests/integration/test_scenarios.py (simplified)
@pytest.mark.asyncio
async def test_1_1_admin_full_access(async_client, admin_token):
    response = await async_client.post(
        "/actions/workday.hcm/get_employee_full",
        json={"parameters": {"employee_id": "EMP001"}},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
```

## Considerations

- Session-scoped fixtures are shared across tests - ensure no mutation
- Some tests may need fresh fixtures (use function scope for those)
- Document fixtures with clear docstrings
- Consider factory fixtures for customizable tokens

## Related Improvements
- None

---
*Identified: 2026-02-01*
