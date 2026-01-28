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

All actions require an OIDC token. For local development with `MockOktaProvider`, use any string as a token. The *subject* and *claims* help determine permissions.

### 1. HCM: Get Employee (Public Directory)
```bash
curl -X POST http://localhost:8000/actions/workday.hcm/get_employee \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "parameters": {
      "employee_id": "EMP001"
    }
  }'
```

### 2. Time: Check Balance (Self-Service)
```bash
curl -X POST http://localhost:8000/actions/workday.time/get_balance \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EMP001" \
  -d '{
    "parameters": {
      "employee_id": "EMP001"
    }
  }'
```

### 3. Time: Request Time Off
```bash
curl -X POST http://localhost:8000/actions/workday.time/request \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer EMP001" \
  -d '{
    "parameters": {
      "employee_id": "EMP001",
      "type": "PTO",
      "start_date": "2026-03-01",
      "end_date": "2026-03-05",
      "hours": 40
    }
  }'
```

### 4. Payroll: Get Compensation (MFA Required)
*Note: Requires token with `amr: ["mfa"]` claim. In mock provider, any token with `mfa` in string or configured via mock issuer.*
```bash
curl -X POST http://localhost:8000/actions/workday.payroll/get_compensation \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-mfa" \
  -d '{
    "parameters": {
      "employee_id": "EMP001"
    }
  }'
```

### Verification
Check the audit log at `logs/audit.jsonl` to see the execution trace and PII redaction.