# Functional Documentation: Workday Simulator

The Workday Simulator provides a realistic, safe environment for developing and testing HR AI capabilities without exposing sensitive real-world data or requiring a live Workday connection.

## Why we use a Simulator

1.  **Safety**: We can test automated terminations or compensation changes without risk to real employees.
2.  **Auth Testing**: It allows us to "stress test" our security policies by simulating different roles (Manager vs. Employee).
3.  **Speed**: No network latency to external Workday servers during development.
4.  **Edge Cases**: We can easily create "unhappy" paths, like insufficient leave balances, to see how the AI handles errors.

## Supported HR Domains

### 1. HCM (Human Capital Management)
Simulates core employee record management:
*   **Employee Directory**: Looking up basic profile info.
*   **Org Structure**: Visualizing reporting lines and department hierarchies.
*   **Manager Chains**: Understanding the path from an individual contributor up to the CEO.
*   **Lifecycle**: Updating profile details and triggering termination workflows.

### 2. Time Tracking
Simulates leave management workflows:
*   **Balances**: Real-time tracking of PTO and Sick Leave.
*   **Requests**: Submitting new time-off requests.
*   **Approvals**: The multi-step flow where a manager reviews and approves a request, automatically updating the employee's balance.

### 3. Payroll
Simulates sensitive compensation data:
*   **Salary Info**: Viewing base salary, bonuses, and equity grants.
*   **Pay Statements**: Generating detailed pay slips with tax breakdowns and net pay.

## Test Personas

We provide a set of pre-configured identities in our "fixtures" to test various scenarios:

| ID | Name | Role | Purpose |
|----|------|------|---------|
| `EMP001` | Alice Johnson | Senior Engineer | The primary test user for self-service actions. |
| `EMP042` | Bob Martinez | Engineering Manager | Used to test manager approvals and team visibility. |
| `EMP100` | Carol Chen | VP Engineering | Used to test deep manager chains and org charts. |
| `EMP200` | Diana Ross | CEO | The root of the organization. |

## How to perform a "Reset"
If you have modified data during a demo or test session and want to return to the original "Golden State," you can trigger a full service reload (clearing all caches and re-reading files) by calling:
`POST /demo/reset`
*(Note: Requires `ENABLE_DEMO_RESET=true` environment variable).*

