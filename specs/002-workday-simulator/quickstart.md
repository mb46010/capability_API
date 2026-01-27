# Quickstart: Workday Simulator

This guide explains how to configure and use the Workday Simulator.

## Configuration

The simulator is configured via `config/policy-workday.yaml` (for permissions) and internal fixture files.

### 1. Policies
Ensure `config/policy-workday.yaml` is loaded by the application. This file defines the capabilities required for each simulated operation.

### 2. Fixtures
Employee data is loaded from YAML files in `src/adapters/workday/fixtures/`. 
Default fixtures are provided for:
- Employees (Alice Johnson, Bob Martinez, etc.)
- Time Off Requests
- Pay Statements

## Usage

### Integration in Code

```python
from src.adapters.workday.client import WorkdaySimulator
from src.adapters.workday.config import WorkdaySimulationConfig

# Initialize simulator
config = WorkdaySimulationConfig(
    base_latency_ms=50,
    failure_rate=0.0
)
workday = WorkdaySimulator(config)

# Call operations
employee = await workday.get_employee("EMP001")
print(employee.name.display)
```

### API Access

If exposed via the API routes (e.g., `/api/workday/...`), you can use standard HTTP requests.

```bash
# Get employee (assuming route exists)
curl http://localhost:8000/api/workday/employees/EMP001
```

## Testing Scenarios

### Latency Injection
Modify the configuration to test timeouts:
```python
config.base_latency_ms = 5000  # 5 seconds
```

### Failure Injection
Test error handling by increasing failure rates:
```python
config.failure_rate = 0.5  # 50% failure rate
```
