# Domain Entities Context

## Purpose
Defines the core data structures for the Capability API.

## Core Models

### Action Protocol
- `ActionRequest`: Standard envelope for all action inputs.
  - `parameters`: Dict of arguments specific to the action.
  - `dry_run`: Boolean to simulate execution without side effects.

- `ActionResponse`: Standard envelope for all action outputs.
  - `data`: The actual result payload (Dict or List).
  - `meta`: Metadata wrapper containing `provenance`.

- `Provenance`: Audit trail metadata.
  - `source`: Originating adapter/system.
  - `timestamp`: Execution time (UTC).
  - `trace_id`: Unique correlation ID.
  - `latency_ms`: Execution duration.
  - `actor`: Principal ID who invoked the action.

## Shared Types
- `Money`: {amount, currency, frequency}
- `EmployeeReference`: {employee_id, display_name}
