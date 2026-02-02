# capability_API Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-01-25

## Active Technologies
- Python 3.11+ + Pydantic V2 (models), PyYAML (fixtures) (002-workday-simulator)
- In-memory with YAML file persistence (read-only fixtures) (002-workday-simulator)
- Markdown (GFM), Mermaid.js + None (Project uses Python 3.11+, Pydantic V2) (003-documentation)
- Local Filesystem (003-documentation)
- Python 3.11+ + FastAPI, Pydantic V2, Authlib (for OIDC) (004-workday-actions)
- In-memory (Workday Simulator) with YAML fixtures for persistence (004-workday-actions)
- Python 3.11+ + FastMCP >= 3.0.0b1, httpx, pydantic-settings, PyJWT (for token inspection) (005-hr-mcp-server)
- N/A (Stateless adapter/gateway) (005-hr-mcp-server)
- Python 3.11+ + Pydantic V2, PyYAML, Jinja2, Tabulate (008-policy-verification)
- Local Filesystem (YAML scenarios, JSON/HTML/JUnit results) (008-policy-verification)
- Python 3.11+ (Core/Scripts), TypeScript/Node.js 18+ (Backstage Plugins) (009-backstage-governance)
- Filesystem (Catalog/TechDocs), API Proxy (Audit Logs) (009-backstage-governance)

- Python 3.11+ + FastAPI, Pydantic V2, Authlib (tentative), MCP SDK (001-capability-api)

## Project Structure

```text
src/
tests/
```

## Commands

cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style

Python 3.11+: Follow standard conventions

## Recent Changes
- 009-backstage-governance: Added Python 3.11+ (Core/Scripts), TypeScript/Node.js 18+ (Backstage Plugins)
- 008-policy-verification: Added Python 3.11+ + Pydantic V2, PyYAML, Jinja2, Tabulate
- 005-hr-mcp-server: Added Python 3.11+ + FastMCP >= 3.0.0b1, httpx, pydantic-settings, PyJWT (for token inspection)


<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
