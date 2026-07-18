# RailYatra AI Platform
# Phase 6 Engineering Constitution
## Enterprise Architecture Governance & Quality Specification

---

## Document Control
- **Document Reference**: RY-P6-ENG-CONST-1.0
- **Version**: 1.0.0
- **Classification**: Internal Enterprise Confidential
- **Status**: APPROVED / ACTIVE
- **Target Audience**: Core Architecture Board, Engineering Leads, Implementation AI Agents

---

## Table of Contents
1. [Introduction and Scope](#1-introduction-and-scope)
2. [Core Engineering Principles](#2-core-engineering-principles)
3. [Discovery Policy](#3-discovery-policy)
4. [Planning Policy](#4-planning-policy)
5. [Architecture Freeze Policy](#5-architecture-freeze-policy)
6. [Implementation Policy](#6-implementation-policy)
7. [Documentation Policy](#7-documentation-policy)
8. [Repository and Package Standards](#8-repository-and-package-standards)
9. [Testing Policy and Quality Gates](#9-testing-policy-and-quality-gates)
10. [Audit Policy](#10-audit-policy)
11. [Completion Patch Policy](#11-completion-patch-policy)
12. [Git and Branch Governance](#12-git-and-branch-governance)
13. [Change Management Procedures](#13-change-management-procedures)
14. [AI Agent Prompt Governance & Rules](#14-ai-agent-prompt-governance--rules)
15. [Definition of Done](#15-definition-of-done)

---

## 1. Introduction and Scope
This document constitutes the official **Engineering Constitution** for **Phase 6** of the RailYatra AI Platform. All subsequent software design, documentation, implementation, testing, and auditing within Phase 6 must adhere strictly to the governance policies, directories, and architectural rules defined herein.

This constitution aims to prevent planning drift, documentation scattering, and architectural decay. It is the single source of truth for engineering execution.

---

## 2. Core Engineering Principles
The platform must be designed and implemented in strict compliance with the following software engineering paradigms:

- **Clean Architecture**: Strong isolation between the core Domain layer (business entities, interfaces), the Application layer (use cases, coordinators, orchestrators), and the Infrastructure layer (databases, API clients, cache implementations).
- **Domain-Driven Design (DDD)**: Explicit identification of domain aggregates, entities, value objects, and domain events.
- **SOLID Principles**: Focus on Single Responsibility, Dependency Inversion (programming to interfaces/protocols), and Open-Closed principles.
- **Composition over Inheritance**: Prefer object composition and strategy delegation over deep class inheritance hierarchies.
- **Provider Independence**: Core intelligence logic must remain completely decoupled from third-party vendor APIs, service endpoints, or GDS systems. All integrations must route through read-only adapters.

---

## 3. Discovery Policy
The Discovery phase establishes the logical business boundaries and domain research before any planning or coding occurs.

### 3.1 Rules and Workflow
- **Frequency**: A Discovery document must be generated exactly once per milestone. Re-generation or revision during subsequent phases is strictly forbidden.
- **Required Sections**:
  - Executive Summary & Scope
  - Domain Vision & System Boundaries
  - Canonical Domain Model Definitions
  - Entity-Relationship Diagram (Mermaid)
- **Approval Workflow**: Must be reviewed and signed off by the Architecture Review Board (ARB).
- **Freeze Policy**: Once approved, the Discovery document is frozen. No modifications are permitted unless an ARB-verified defect is discovered.

---

## 4. Planning Policy
The Planning phase translates the Discovery specifications into concrete engineering designs and interfaces.

### 4.1 Rules and Workflow
- **Frequency**: Generated exactly once per milestone. No code implementation may begin until the Planning blueprint is frozen.
- **Required Sections**:
  - Package Structure & Folder Map
  - Subsystem Catalog (Input, Output, Failure Modes)
  - Abstract Interface Contracts (Python Protocols or ABCs)
  - Domain Transfer Object (DTO) Schemas
  - Validation & Latency Budgets
- **Dependency Flow**: The blueprint must explicitly define inward-only dependencies from outer layers to core domain entities.

---

## 5. Architecture Freeze Policy
The Architecture Freeze locks the technical design of a milestone to prevent refactoring loop cycles during implementation.

### 5.1 Freeze Workflow
- **Trigger**: Occurs immediately upon the formal ARB approval of the Planning blueprint.
- **Effect**: Complete freeze on class design, package layouts, and DTO schemas.
- **Allowed Modifications**: Changes are only permitted to resolve verified compiler errors, dependency collisions, or test regressions. Redesigning architecture or expanding scope is forbidden.

---

## 6. Implementation Policy
The Implementation phase is strictly transactional, converting frozen planning designs into executable source code.

### 6.1 Rules and Workflow
- **Sequence**:
  1. Read the frozen Discovery document.
  2. Read the frozen Planning document.
  3. Implement the planned scopes in small, logical steps.
  4. Generate the technical walkthrough.
  5. Run test verification and static analysis checks.
- **Constraints**: Implementation prompts/agents are forbidden from planning, rewriting specifications, or adding business features that were not explicitly scoped.

---

## 7. Documentation Policy
To prevent scattered files, all documentation files for Phase 6 must adhere to a standardized directory layout and naming convention.

### 7.1 Directory Organization
All documentation relating to Phase 6 milestones must reside under:
`docs/phase6/milestone_x_x/`

### 7.2 Standard Deliverables per Milestone
- `docs/phase6/milestone_x_x/Discovery.md`
- `docs/phase6/milestone_x_x/Planning.md`
- `docs/phase6/milestone_x_x/Technical_Walkthrough.md`
- `docs/phase6/milestone_x_x/Implementation_Report.md`
- `docs/phase6/milestone_x_x/Audit_Report.md`

---

## 8. Repository and Package Standards
- **Folder Names**: Lowercase, single-word directories (e.g. `gateway/`, `orchestrator/`, `confidence/`).
- **File Names**: Snake_case (e.g. `engine.py`, `contracts.py`, `models.py`).
- **Interfaces**: Reside in `interfaces/contracts.py` or `interfaces/protocols.py`. Concrete modules must import interfaces directly.
- **DTOs**: Placed under `dto/models.py`.

---

## 9. Testing Policy and Quality Gates
A milestone is not considered complete until all operational quality gates are green.

### 9.1 Quality Gates
- **Static Analysis (Ruff Linter)**: Must pass with zero errors.
- **Auto-Formatting (Ruff Formatter)**: Codebase must comply with formatting rules.
- **Type Checking (MyPy)**: Zero type issues across all packages.
- **Test Executions (PyTest)**: 100% pass rate.
- **Regression Checks**: Prior milestone tests must not break.

---

## 10. Audit Policy
The Enterprise Architecture Compliance Audit validates the completed milestone against Discovery and Planning documents.

### 10.1 Required Artifacts
The audit results must be compiled into the following deliverables:
- `docs/phase6/milestone_x_x/Compliance_Report.md`
- `docs/phase6/milestone_x_x/Completion_Patch.md` (only if corrections were made)

---

## 11. Completion Patch Policy
A Completion Patch is the only mechanism permitted to resolve compliance gaps found during audits.

### 11.1 Patch Rules
- Must contain the absolute minimum code changes needed to satisfy planning boundaries.
- Refactoring healthy modules or introducing new features in a patch is strictly forbidden.
- All tests must be re-run and pass after a patch is applied.

---

## 12. Git and Branch Governance
- **Branch Naming**: `feat/p6-mx-x-description` or `fix/p6-mx-x-description`.
- **Commit Messages**: Standard conventional commits (e.g., `feat(personalization): implement preference validation`, `fix(pipeline): resolve timeout race condition`).
- **PR Merging**: Only squash-merge to the main branch after all CI quality gate tests pass.

---

## 13. Change Management Procedures
1. **Proposal**: Submit a modification request to the ARB detailing the file paths, code diffs, and architectural impact.
2. **Review**: ARB evaluates the impact on dependencies and system latency budgets.
3. **Approval**: If approved, update the affected Planning document version history and release the lock.

---

## 14. AI Agent Prompt Governance & Rules
When coordinating work with AI agents, the following principles apply:
- **Single Responsibility Prompts**: A prompt must carry exactly one action code (e.g., Discovery research ONLY, planning design ONLY, code implementation ONLY, auditing ONLY).
- **Execution Guardrails**: The implementation agent must fail-fast and report immediately if any requirements or interfaces are missing or ambiguous, instead of guessing.

---

## 15. Definition of Done
A Phase 6 milestone is completed only when:
- [ ] Discovery and Planning documents are frozen and archived.
- [ ] Code implementation maps 1-to-1 to interfaces and DTOs.
- [ ] PyTest, Ruff check, and MyPy pass with zero errors.
- [ ] An Enterprise Architecture Audit is conducted and all gaps are closed.
- [ ] Git working tree is clean and changes are pushed to main branch.
- [ ] Sign-off is formally granted by the ARB.
