# Data Model: Documentation Metadata

This feature does not introduce new database entities but enhances existing Pydantic models with descriptive metadata.

## Metadata Standards

### Pydantic Fields
Every field in a `domain/entities` or `adapters/*/domain` model must include:
- **Type Hinting**: Explicit PEP 484 types.
- **Description**: A `Field(description="...")` string.
- **Example**: `Field(examples=[...])` where beneficial.

### Module Metadata (README.ai.md)
Each module must define its:
- **Sovereignty**: What it is responsible for.
- **Dependencies**: List of internal and external modules it depends on.
- **Ports**: Interfaces implemented or consumed.
- **Constraints**: Local architectural rules.
