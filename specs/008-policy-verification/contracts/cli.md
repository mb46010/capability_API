# CLI Contract: verify-policy

## Commands

### `run`
Executes verification tests.

**Arguments**:
- `--policy <path>`: Path to policy YAML (default: `config/policy-workday.yaml`).
- `--scenarios <dir|file>`: Path to scenarios (default: `tests/policy/scenarios/`).
- `--format <table|json|junit>`: Output format.
- `--output <path>`: Output file for machine-readable formats.

**Exit Codes**:
- `0`: All tests passed.
- `1`: One or more tests failed.
- `2`: Configuration or schema error.

### `list-scenarios`
Lists all available test scenarios and their metadata.

### `coverage` (Optional)
Reports which capabilities in the registry lack verification tests.
