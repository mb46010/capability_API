# Research Findings - Capability Registry

**Feature**: Capability Registry (`007-capability-registry`)
**Status**: Research Complete

## 1. Logging Pattern

**Context**: Need to ensure deprecation warnings follow the project standard.
**Findings**:
- The project uses a custom `PIIMaskingFormatter` defined in `src/lib/logging.py`.
- The setup is global via `setup_logging()`.
- Modules should use `logging.getLogger(__name__)`.
- **Decision**: In `ActionService`, use `logger = logging.getLogger(__name__)` and `logger.warning("...")` for deprecation messages. This automatically applies PII masking and request ID context.

## 2. Directory Structure & Imports

**Context**: Avoid circular dependencies between Policy Loader, Action Service, and Registry.
**Findings**:
- `ActionService` (`src/domain/services/action_service.py`) and `FilePolicyLoaderAdapter` (`src/adapters/filesystem/policy_loader.py`) are consumers of the Registry.
- `CapabilityRegistryService` (`src/domain/services/capability_registry.py`) is a leaf node (dependency-wise).
- **Structure**:
    - `src/domain/entities/capability.py`: Pydantic models.
    - `src/domain/services/capability_registry.py`: Service logic + Loader (monolithic). Imports `entities/capability.py`.
    - `src/adapters/filesystem/policy_loader.py`: Imports `capability_registry.py`.
    - `src/domain/services/action_service.py`: Imports `capability_registry.py`.
- **Decision**: This DAG is clean. No circular dependencies.

## 3. Dependency Management

**Context**: PRD mentions `tabulate` for CLI output.
**Findings**:
- `tabulate` is missing from `requirements.txt`.
- **Decision**: Add `tabulate>=0.9.0` to `requirements.txt`.

## 4. Singleton Pattern

**Context**: Efficient loading of registry (read-once).
**Findings**:
- PRD suggests `functools.lru_cache`.
- **Decision**: Use `@lru_cache(maxsize=1)` on a factory function `get_capability_registry(path: str)` in `src/domain/services/capability_registry.py`. This is simple and effective for this scale.

## 5. Registry Path Consistency

**Context**: Ensuring `ActionService` and `AppSettings` use the same registry file.
**Findings**:
- `AppSettings` in `src/lib/config_validator.py` defines the source of truth for paths.
- `ActionService` currently assumes hardcoded behaviors.
- **Decision**: `ActionService` should accept `capability_registry: CapabilityRegistryService` in its `__init__`, allowing dependency injection from `main.py` where `AppSettings` are available. This is better than `ActionService` guessing the path.
