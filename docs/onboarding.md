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

## Running Tests
We use `pytest` for all tests.

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run integration tests only
pytest tests/integration/
```

## Key Documentation to Read
1. **Architecture**: `docs/architecture.md`
2. **Constitution**: `.specify/memory/constitution.md`
3. **Workflow**: `specs/` directory for feature-specific plans.
