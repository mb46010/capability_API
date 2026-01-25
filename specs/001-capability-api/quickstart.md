# Quickstart: HR AI Platform Capability API

## Prerequisites
- Python 3.11+
- [LocalStack](https://localstack.cloud/) (optional, for S3/StepFunctions simulation)
- A local Okta issuer (or mock)

## Setup
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv && source venv/bin/activate`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Run the local mock server: `python src/api/main.py`.

## Running Locally
By default, the API starts with `LocalAdapter` for storage and flows.

### 1. Execute an Action
```bash
curl -X POST http://localhost:8000/actions/workday.get_employee \
  -H "Authorization: Bearer <MOCK_OKTA_TOKEN>" \
  -d '{"employee_id": "12345"}'
```

### 2. Start a Flow
```bash
curl -X POST http://localhost:8000/flows/hr.onboarding/start \
  -H "Authorization: Bearer <MOCK_OKTA_TOKEN>" \
  -d '{"name": "Jane Doe", "start_date": "2026-02-01"}'
```

### 3. Check Flow Status
```bash
curl http://localhost:8000/flows/executions/<EXECUTION_ID>/status \
  -H "Authorization: Bearer <MOCK_OKTA_TOKEN>"
```

## Policy YAML
Modify `policy/access_control.yaml` to change scope-to-action mappings. Changes are picked up automatically in development mode.

```