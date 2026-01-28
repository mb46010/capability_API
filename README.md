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

Once running, you can test the API using our helper scripts:
```bash
./scripts/api/smoke-test.sh
```

The API will be available at:
- Docs: http://localhost:8000/docs
- OpenAPI: http://localhost:8000/openapi.json

### Testing

Run the full test suite:

```bash
pytest
```

## Documentation Index

Explore the project's documentation for deeper insights into architecture, onboarding, and troubleshooting.

### For Humans
- **[Architectural Guide](docs/architecture.md)**: High-level system design and hexagonal boundaries.
- **[Onboarding Guide](docs/onboarding.md)**: Environment setup and developer workflow.
- **[API Layer Overview](src/api/docs/overview.md)**: Design philosophy and core components of the public surface.
- **[API Getting Started](src/api/docs/getting_started.md)**: Quick guide to running, authenticating, and testing the API.
- **[Workday Technical Docs](src/adapters/workday/docs/technical.md)**: Deep-dive into the Workday simulator implementation.
- **[Workday Functional Docs](src/adapters/workday/docs/functional.md)**: Business overview of simulation data and personas.
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and their resolutions.
- **[Project Constitution](.specify/memory/constitution.md)**: The core principles governing this project.

### For AI Agents
Distributed `README.ai.md` files provide high-density functional context for coding agents:
- [Domain Core](src/domain/services/README.ai.md)
- [Hexagonal Ports](src/domain/ports/README.ai.md)
- [Workday Adapter](src/adapters/workday/README.ai.md)
- [Auth Provider](src/adapters/auth/README.ai.md)
- [Filesystem Implementation](src/adapters/filesystem/README.ai.md)
- [API Layer](src/api/README.ai.md)
- [Common Library](src/lib/README.ai.md)

## Adding a Capability

1. Define the capability logic in `src/domain/services/action_service.py` (or a dedicated domain service).
2. Add the implementation in `src/adapters/connectors/`.
3. Update `config/policy.yaml` to grant access to your principal.
4. Restart the server.
