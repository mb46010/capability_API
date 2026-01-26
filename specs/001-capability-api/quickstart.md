# Quickstart: Capability API

**Status**: Draft
**Date**: 2026-01-26

## Prerequisites
- Python 3.11+
- Docker (optional, for running dependencies like LocalStack if needed later)

## Setup

1. **Clone & Navigate**
   ```bash
   git checkout 001-capability-api
   cd src
   ```

2. **Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configuration**
   Create a `.env` file in the root:
   ```bash
   LOG_LEVEL=INFO
   ENVIRONMENT=local
   POLICY_PATH=./config/policy.yaml
   OKTA_ISSUER=https://mock-okta.local
   ```

## Running the API

Start the FastAPI server locally:

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at:
- Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

## Testing

Run the test suite (includes unit and contract tests):

```bash
pytest
```

## Adding a Capability

1. Define the capability in `src/domain/capabilities.py`.
2. Add the implementation in `src/adapters/connectors/`.
3. Update `config/policy.yaml` to grant access to your principal.
4. Restart the server (or rely on auto-reload).
