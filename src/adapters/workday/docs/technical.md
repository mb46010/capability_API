# Technical Documentation: Workday Simulator

This document provides a deep dive into the implementation of the Workday Simulator adapter.

## Architecture

The simulator is implemented as a **Hexagonal Adapter** that fulfills the `ConnectorPort` interface. It is designed to be a "plug-and-play" replacement for a real Workday integration.

### Core Components

1.  **`WorkdaySimulator` (client.py)**: The main entry point. It handles action dispatching, latency simulation, and failure injection.
2.  **`FixtureLoader` (loader.py)**: Responsible for reading YAML files and instantiating Pydantic models. It performs a **two-pass resolution** to link manager references correctly.
3.  **Domain Services (services/)**:
    *   `WorkdayHCMService`: Logic for employee data and organization structure.
    *   `WorkdayTimeService`: Logic for leave balances and request lifecycles.
    *   `WorkdayPayrollService`: Logic for compensation and pay statements.

## In-Memory State

Unlike a stateless proxy, this simulator maintains a **mutable in-memory state**.
- Changes made via `update_employee` or `request_time_off` are stored in the current process memory.
- **Persistence**: State is volatile and resets when the server restarts.
- **Reloading**: The `/actions/test/reload-fixtures` endpoint allows refreshing the state from the YAML files without a restart.

## Simulation Features

### 1. Latency Injection
The simulator calculates a delay for every operation based on the `WorkdaySimulationConfig`:
- **Base Latency**: 50ms (default).
- **Variance**: +/- 50ms.
- **Write Multiplier**: Operations that modify state (e.g., `approve`, `terminate`) are multiplied by 3.0 to simulate slower write-consistency in distributed systems.

### 2. Failure Injection
To test system resilience, the simulator supports configurable failure rates:
- `failure_rate`: Probability (0.0 - 1.0) of returning a `CONNECTOR_UNAVAILABLE` (503) error.
- `timeout_rate`: Probability of raising a `CONNECTOR_TIMEOUT` (504) error.

## Adding New Operations

1.  **Define Model**: Add the Pydantic schema to `src/adapters/workday/domain/`.
2.  **Update Fixture**: Add sample data to the relevant YAML in `src/adapters/workday/fixtures/`.
3.  **Implement Logic**: Add a method to the appropriate service class in `services/`.
4.  **Register Action**: The `WorkdaySimulator.execute` method uses `getattr` to automatically find methods in its service sub-classes. Ensure the method name matches the suffix of the capability string (e.g., `get_employee`).

## Testing
Unit tests for the loader are in `tests/unit/adapters/workday/`. Integration tests covering the full request lifecycle through the API are in `tests/integration/adapters/workday/`.
