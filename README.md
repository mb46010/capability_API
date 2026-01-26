# HR AI Platform Capability API

Governed API exposing deterministic actions and long-running HR flows.

## Quickstart

### Prerequisites
- Python 3.11+
- Docker (optional)

### Setup

1. **Clone & Navigate**
   ```bash
   git clone <repo-url>
   cd src
   ```

2. **Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Configuration**
   Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

### Running the API

Start the FastAPI server locally:

```bash
uvicorn src.main:app --reload --port 8000
```

The API will be available at:
- Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

### Testing

Run the full test suite:

```bash
pytest
```

## Adding a Capability

1. Define the capability logic in `src/domain/services/action_service.py` (or a dedicated domain service).
2. Add the implementation in `src/adapters/connectors/`.
3. Update `config/policy.yaml` to grant access to your principal.
4. Restart the server.
