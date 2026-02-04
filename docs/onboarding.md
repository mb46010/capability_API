# Developer Onboarding Guide

Welcome to the Capability API project! This guide will help you set up your local development environment.

## Prerequisites
- **Python**: 3.11 or higher.
- **Git**: For version control.

## Setup Instructions

### 1. Clone the Repository
```bash
git clone <repo-url>
cd capability_API
```

### 2. Create a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configuration
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Ensure `POLICY_PATH` points to `config/policy-workday.yaml` for local development.

### 5. Running the API
```bash
python -m src.main
```
The API will be available at `http://localhost:8000`. You can view the interactive documentation at `http://localhost:8000/docs`.

## Environment Flags
- `ENVIRONMENT`: `local` | `dev` | `prod` | `test`
- `POLICY_PATH`: `config/policy-workday.yaml` (default)
- `MOCK_OKTA_TEST_SECRET`: Secret key for mock Okta test endpoints (REQUIRED).
- `ENABLE_DEMO_RESET`: `true` | `false` (mounts demo reset endpoint; local only)

## Running Tests
We use `pytest` for all tests.

```bash
# Quick tests (unit only)
pytest tests/unit/

# Run all tests
pytest
```

## Governance & Documentation
If you modify the Capability Registry (`config/capabilities/index.yaml`), you must regenerate the Backstage catalog:
```bash
python3 scripts/generate_catalog.py
```

To build and patch the documentation (fixes diagrams):
```bash
./scripts/make_docs.sh
```

To view the local governance docs:
```bash
mkdocs serve
```

## Key Documentation to Read
1. **Architecture**: `docs/architecture.md`
2. **Backstage Integration**: `docs/backstage.md`
3. **API Usage**: `docs/api_usage.md`
4. **Constitution**: `.specify/memory/constitution.md`
