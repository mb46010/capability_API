# Capability API

Governed surface exposing deterministic actions and flow triggers for the HR AI Platform.

## 🎯 Motivation
**New to the project?** Read our **[Motivation & Business Value Guide](docs/motivation.md)** to understand what we are building, why it matters for HR and AI safety, and what to expect in a demo.

## 🏗️ Architecture
The system follows a **Hexagonal Architecture** (Ports and Adapters) to isolate core HR business logic from external systems like Workday or Okta.

- **Domain Core**: Policy evaluation, action routing, and flow orchestration.
- **Adapters**: Workday Simulator, Mock Okta (OIDC), and Local Filesystem persistence.
- **API Surface**: Unified FastAPI surface for Actions and Flows with built-in audit provenance.

## 🚀 Quickstart

### Prerequisites
- Python 3.11+
- `pip`

### Setup

1. **Clone & Install**
   ```bash
   git clone <repo-url>
   pip install -r requirements.txt
   ```

2. **Run the API**
   Start the FastAPI server locally:
   ```bash
   python -m src.main
   ```

3. **Verify**
   Check the system health:
   ```bash
   curl http://localhost:8000/health
   ```

### 📺 Interactive Demo
We provide a suite of demo scripts to showcase AI guardrails, token exchange, and policy safety:
```bash
./scripts/demo/run-full-demo.sh
```

### 🧪 Testing & Validation
Quick tests (unit only):
```bash
pytest tests/unit/
```

Run the full test suite:
```bash
pytest
```

Run the policy verification suite:
```bash
./scripts/verify-policy run
```

### ⚙️ Environment Flags
- `ENVIRONMENT`: `local` | `dev` | `prod` | `test`
- `POLICY_PATH`: `config/policy-workday.yaml` (default)
- `MOCK_OKTA_TEST_SECRET`: Secret key for mock Okta test endpoints (REQUIRED).
- `ENABLE_DEMO_RESET`: `true` | `false` (mounts demo reset endpoint; local only)

## 📚 Documentation Index

### For Humans (Project & Governance)
- **[Motivation & Value](docs/motivation.md)**: The "Why" and business context.
- **[Architectural Guide](docs/architecture.md)**: System design and hexagonal boundaries.
- **[Security Architecture](docs/security_architecture.md)**: Defense-in-depth and MFA enforcement.
- **[Policy Schema](docs/policy_schema.md)**: Rules for defining access control.
- **[Policy Verification](docs/modules/policy_verification.md)**: How we prove policies work.
- **[Token Exchange](docs/modules/token_exchange.md)**: Secure cross-system identity delegation.
- **[Capability Registry](docs/CAPABILITY_REGISTRY.md)**: Discovery of available Actions and Flows.

- **[Workday Simulator](docs/modules/workday_technical.md)**: Details on the high-fidelity HRIS simulation.
- **[Onboarding Guide](docs/onboarding.md)**: Detailed setup for developers.
- **[Troubleshooting](docs/troubleshooting.md)**: Common issues and fixes.
- **[Project Constitution](.specify/memory/constitution.md)**: Core principles and development standards.

### For AI Agents (Technical Context)
Distributed `README.ai.md` files provide functional context for coding agents:
- **[Domain Entities](src/domain/entities/README.ai.md)**: Data models and validation rules.
- **[Domain Services](src/domain/services/README.ai.md)**: Core business logic and verification runner.
- **[Hexagonal Ports](src/domain/ports/README.ai.md)**: Abstract interfaces for infrastructure.
- **[Workday Adapter](src/adapters/workday/README.ai.md)**: HRIS simulation implementation.
- **[Auth Provider](src/adapters/auth/README.ai.md)**: OIDC mock and JWT verification.
- **[Filesystem Implementation](src/adapters/filesystem/README.ai.md)**: Local storage for policies.
- **[API Layer](src/api/README.ai.md)**: Routing and dependency injection.
- **[Common Library](src/lib/README.ai.md)**: Logging, context, and shared utilities.

## 🛠️ Adding a Capability

1.  **Registry**: Add the capability to `config/capabilities/index.yaml`.
2.  **Logic**: Implement the logic in `src/domain/services/` or `src/domain/entities/`.
3.  **Adapter**: Update the Workday Simulator or relevant adapter.
4.  **Policy**: Grant access in `config/policy-workday.yaml`.
5.  **Verify**:
    - Validate Registry: `./scripts/capability-registry validate`
    - Verify Security: `./scripts/verify-policy run`
    - Run Tests: `pytest`
