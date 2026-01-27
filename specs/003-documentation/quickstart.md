# Quickstart: Constitutional Documentation

This guide explains how to use and maintain the project's documentation in accordance with Article VI of the Capability API Constitution.

## Finding Documentation

### For Humans
- **Architecture**: See `docs/architecture.md` for high-level system design and hexagonal boundaries.
- **Onboarding**: Start with `docs/onboarding.md` to set up your environment.
- **Troubleshooting**: Visit `docs/troubleshooting.md` for common issues and their resolutions.
- **API Reference**: The root `README.md` now includes an index of all major guides.

### For AI Agents
- Look for `README.ai.md` in any logic-centric module (e.g., `src/domain/services/README.ai.md`). These files provide high-density facts and dependency mappings optimized for LLM context.

## Documentation Standards

### Pydantic Models
When creating or modifying models, ensure every field has a description:
```python
from pydantic import Field

class Employee(BaseModel):
    employee_id: str = Field(description="Unique identifier for the employee (e.g., EMP001)")
```

### Module READMEs
Add a `README.ai.md` to any new logic-centric directory. It should contain:
1. **Purpose**: 1-2 sentences.
2. **Key Exports**: Principal functions or classes.
3. **Dependencies**: External ports or internal modules.
4. **Constraints**: Local architectural rules.

## Maintenance
- Documentation should be updated in the same PR as the code changes (Documentation as Code).
- Re-run `/speckit.analyze` to ensure documentation consistency across the project.
