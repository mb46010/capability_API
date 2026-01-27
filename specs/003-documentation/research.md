# Research Findings: Documentation Standards

**Feature**: 003-documentation
**Date**: 2026-01-27

## Summary
The goal is to define and implement documentation standards that satisfy both human and AI consumers, as mandated by the project constitution.

## Findings

### 1. README.ai.md Best Practices
Research into coding agent optimizations (e.g., Cursor, Windsurf, Gemini) suggests that AI READMEs should focus on:
- **High-Density Information**: Minimal prose, maximal facts.
- **Dependency Graphs**: Explicitly listing local imports and external ports.
- **Constraint Lists**: Enumerating architectural "rules" for the specific module.
- **Schema Mapping**: Linking to Pydantic models.

### 2. Pydantic Self-Documentation
Pydantic V2 supports the `Field` class with a `description` parameter. This metadata is captured in `model_json_schema()` and automatically propagates to FastAPI's OpenAPI generator.
- **Decision**: All model fields must have a `description` if they are not self-evident.

### 3. Architectural Diagrams
Mermaid.js is the preferred choice for Markdown-integrated diagrams.
- **Decision**: Use `C4` or standard `graph TD` diagrams in `docs/architecture.md`.

## Next Steps
- Define templates for `README.ai.md`.
- Identify all `src/` subdirectories requiring documentation.
- Review all entities for missing descriptions.
