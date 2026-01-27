# Feature Spec: Constitutional Documentation (Article VI)

**Status**: Draft
**Created**: 2026-01-27
**Context**: Correcting constitutional violations regarding missing documentation.

## Clarifications

### Session 2026-01-27
- Q: Which specific directories in `src/` should receive a `README.ai.md`? → A: **Logic-Centric**: Every immediate subdirectory of `src/` and functional children (e.g., `adapters/workday`, `domain/services`).
- Q: What is the requirement for Pydantic field descriptions? → A: **Strict**: Mandatory for every single field in every model to ensure high-quality self-documentation.
- Q: Which diagram types should be prioritized in the Architectural Guide? → A: **C4 Model**: System Context and Container diagrams using Mermaid to clearly show hexagonal boundaries.
- Q: How should module dependencies be documented? → A: **Manual list**: A curated list of internal/external dependencies in each `README.ai.md` optimized for AI context.
- Q: How should documentation assets be indexed? → A: **Unified Index**: A dedicated section in the root `README.md` linking to all major guides and AI READMEs for easy discovery.

## Overview
Article VI of the Capability API Constitution mandates specific documentation standards for both humans and AI agents. This feature aims to bring the repository into compliance by implementing missing `README.ai.md` files, architectural guides, and ensuring all Pydantic models are self-documenting.

## Requirements

### 1. Module-Level Documentation (AI-Optimized)
Every major module must contain a `README.ai.md` providing high-density context for coding agents.
- **Scope**: Every immediate subdirectory of `src/` and their functional children (e.g., `adapters/workday`, `domain/services`).
- **Content**: Purpose, exported symbols, Pydantic schemas, manual dependency list, and local architectural rules.

### 2. Architectural Guide (Human-Oriented)
A high-level guide explaining the "Why" and the overall system design.
- **Location**: `docs/architecture.md`.
- **Content**: C4 Model diagrams (System Context and Container) using Mermaid, hexagonal port/adapter mappings, and core logic flow.

### 3. Self-Documenting Contracts
All Pydantic models must use `Field` descriptions and type hints.
- **Strictness**: Mandatory for every field in every model.
- **Target Files**: All files in `src/domain/entities/` and `src/adapters/workday/domain/`.

### 4. Navigation & Indexing
- **Unified Index**: A dedicated "Documentation" section in the root `README.md` must link to all major guides and distributed AI READMEs.

### 5. Troubleshooting & Onboarding
A guide for developers to get started and fix common issues.
- **Location**: `docs/onboarding.md` and `docs/troubleshooting.md`.

## User Stories
- **US1**: As a developer, I want to see `README.ai.md` in every module so that my AI coding assistant can understand the local context instantly.
- **US2**: As an architect, I want a central architecture document so that the system design is transparent and maintainable.
- **US3**: As a maintainer, I want Pydantic models to have descriptions so that the generated OpenAPI spec is high quality.

## Out of Scope
- Full tutorial videos.
- External wiki migration.