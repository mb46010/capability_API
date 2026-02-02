# Stakeholder Demo Scripts

This directory contains a suite of interactive demo scripts designed to showcase the HR AI Platform's security and governance capabilities to non-technical stakeholders.

## Prerequisites

Before running any demo, ensure the Capability API and Mock Auth services are running:

```bash
# Terminal 1: Core services
python src/main.py
```

## Running the Full Demo

The easiest way to walk through all capabilities is to use the master script:

```bash
./scripts/demo/run-full-demo.sh
```

This script will pause after each module to allow for explanation and discussion.

## Individual Demo Modules

If you want to demonstrate a specific feature, you can run the modules independently:

### 1. AI Guardrails (`demo-1-guardrails.sh`)
- **What it shows**: Field-level data filtering for AI agents and conditional MFA enforcement for sensitive human actions.
- **Why it matters**: Proves that the system protects sensitive PII (like SSNs) from being "seen" by AI models, even if they have directory access.

### 2. Scoped Task Passes (`demo-2-token-exchange.sh`)
- **What it shows**: The RFC 8693 Token Exchange process.
- **Why it matters**: Demonstrates how we reduce the "blast radius" by giving AI models short-lived (5 min), task-specific tokens instead of full user credentials.

### 3. The Safety Net (`demo-3-policy-verification.sh`)
- **What it shows**: The Policy Verification Framework detecting a simulated security violation (human error in a policy file).
- **Why it matters**: Highlights the "Zero trust" commitment—we mathematically prove policies work before they are deployed.

### 4. Compliance Reporting (`demo-4-compliance-report.sh`)
- **What it shows**: Generation of a stakeholder-friendly HTML compliance report.
- **Why it matters**: Provides audit-ready evidence that 100% of defined capabilities are protected by verified security rules.

### 5. Backstage Governance (`demo-5-backstage.sh`)
- **What it shows**: The "Governance Lens" in Backstage.io, including the browsable Capability Catalog, visualized orchestration flows (Mermaid), and the TechDocs policy dashboard.
- **Why it matters**: Makes technical security rules human-browsable and verifiable by anyone in the organization without reading YAML.

## Supporting Tools

- `show-audit.sh`: Tails the live audit log to show real-time provenance and PII masking.
- `policy_report.py`: Utility script for generating textual policy summaries.
- `generate_fixtures.py`: Resets the Workday Simulator's data to its baseline state.
