<!--
Sync Impact Report:
- Version change: 1.0.0 → 1.1.0
- List of modified principles: Added Article VIII: Professional Logging & Privacy.
- Added sections: Article VIII: Professional Logging & Privacy.
- Removed sections: None.
- Templates requiring updates:
    - .specify/templates/plan-template.md: ✅ Updated to include PII masking check.
    - .specify/templates/spec-template.md: ✅ No update required.
    - .specify/templates/tasks-template.md: ✅ Updated foundational task for logging to include PII masking.
- Follow-up TODOs: None.
-->

# Capability API Constitution

## Mission
Build an HR AI Platform whose core product is a governed Capability API: a single, versioned OpenAPI surface exposing deterministic actions and flow triggers. Agents, workflows, admin tools, and user apps are interchangeable clients. **Python-Native:** All core logic shall be written in idiomatic Python, prioritizing readability and the rich data ecosystem. Hexagonal structure: develop local, painlessly move to the cloud.

## Core Principles

### Article I: The Technical Foundation
1) **Product framing and core principle**: Build a governed Capability API where agents and apps are interchangeable clients. Logic must be idiomatic Python. Hexagonal structure is mandatory for cloud portability.
2) **Actions vs flows**: 
   - **Actions**: short-lived, deterministic operations with explicit schemas, idempotency, and audit semantics.
   - **Flows**: long-running HR processes sequencing actions and waiting for human input, without embedding business logic inside agents.

### Article II: Hexagonal Integrity (The Storage Port)
1. **Port & Adapter Pattern**: The "Signal Engine" logic is a protected sanctuary. It shall never know if it’s talking to a local folder or an AWS S3 bucket.
2. **Storage Agnosticism**: Data persistence is handled via a **Storage Port**.
   - **Local-First**: Development and testing happen against the local filesystem.
   - **Seamless Swap**: Moving to the cloud is a configuration change, not a code refactor.
3. **Data Contracts**: Information passing between ports must be validated. No "loose strings" or "blind dictionaries."

### Article III: Operational Rigor
1. **Idempotency by Design**: Running the same process twice must yield the same result. We track what has been "seen" and "done" to avoid duplicate AI processing and data pollution.
2. **The Audit Trail**: Every scrape, "nugget" extracted, and failure must be logged with **provenance**.
3. **Observed Failure**: Retries are automated, alerting is centralized. A silent failure is a constitutional violation.

### Article IV: Development Standards
1. **Test-First (TDD Mindset)**: The first task will be to write tests for "happy path" and "nasty edge cases" before finalizing logic. If it isn't tested, it doesn't work.
2. **Maintainability over Cleverness**: Write code for the "Next Person." Prefer clear, boring code over "clever" one-liners.
3. **Revise and extend tests and docs before delivery** when you think you are done, take one more look at test and documents. Can you make them more extensive and complete? Then do so!

### Article V: Configuration & Environment
1. **Code is Constant, Config is Variable**: No hardcoded URLs, API keys, or folder paths.
2. **Environment-Driven**: Engine behavior is dictated by environment variables and structured config files.
3. **Local Parity**: Local environment must mimic production cloud to ensure "Deploy with Confidence."

## Article VI: The Living Record (Documentation)
1. **Documentation as Code**: Pull Request requirement. No feature is "Done" until human and AI-tailored docs are updated.
2. **Dual-Purpose Documentation**:
   - **For Humans**: High-level "Why" (intent), architectural diagrams, and troubleshooting guides.
   - **For AI (LLM-Optimized)**: High-density "What" and "How." Structured formats (llms.txt, markdown specs) emphasizing Pydantic schemas and rules.
3. **The Onboarding Blueprint**: Every module MUST contain a `README.ai.md` for coding agents.
4. **Self-Documenting Contracts**: Prioritize Type Hints and Pydantic Field Descriptions.

## Article VII: Modular Sovereignty & Maintainability
1. **The Anti-Monolith Pact**: No "God Files." Modules > 300 lines or > 1 responsibility MUST be refactored.
2. **Modular Reusability**: Features (Scrapers, Filters, etc.) designed as standalone utilities for cross-project reuse.
3. **Test-Driven Evolution**: Use tests as executable documentation.

## Article VIII: Professional Logging & Privacy
1. **No Print Statements**: Use of `print()` for debugging or status in production code is forbidden. All output MUST go through the standard logging library.
2. **Crafted for Debugging**: Logs MUST be well-structured, providing sufficient context to diagnose issues without requiring access to the source code.
3. **PII Masking**: Personally Identifiable Information (PII) MUST be masked in all log outputs. This applies to text fields, metadata, and data payloads. A silent PII leak is a constitutional violation.

## Governance
1. **Supremacy**: This Constitution supersedes all other project practices.
2. **Amendments**: Proposed via PR. Requires architectural review. Version must be bumped (MAJOR/MINOR/PATCH).
3. **Compliance**: All PRs must verify compliance with these articles.
4. **Ratification**: The original adoption date is 2026-01-25.

**Version**: 1.1.0 | **Ratified**: 2026-01-25 | **Last Amended**: 2026-01-25
