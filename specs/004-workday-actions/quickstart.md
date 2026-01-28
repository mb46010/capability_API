# Quickstart: Workday Actions

## Prerequisites
- Python 3.11+
- Virtual environment active

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the API server**:
   ```bash
   uvicorn src.main:app --reload
   ```

## Testing Actions

### Using `curl`

All actions require an OIDC token. For local development with `MockOktaProvider`, you can use any string as a token, but the *subject* in the token helps determine permissions.

**1. Get Employee (Public)**
```bash
curl -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d 
    "{
    "parameters": {
      "employee_id": "EMP001"
    }
  }"
```

**2. Check Balance**
```bash
curl -X POST http://localhost:8000/actions/workday.time/get_balance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d 
    "{
    "parameters": {
      "employee_id": "EMP001"
    }
  }"
```

**3. Request Time Off (State Mutation)**
```bash
curl -X POST http://localhost:8000/actions/workday.time/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d 
    "{
    "parameters": {
      "employee_id": "EMP001",
      "type": "PTO",
      "start_date": "2026-03-01",
      "end_date": "2026-03-05",
      "hours": 40
    }
  }"
```

### Verification
Check the audit log at `logs/audit.jsonl` (once implemented) to see the execution trace.
