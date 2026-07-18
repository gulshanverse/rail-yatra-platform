# Repository Audit Report

This document reports on the structural organization, package naming conventions, and file dependencies of Phase 5.

---

## 1. Directory Structure and Package Boundaries

All code relating to Phase 5 is located under `apps/ai-service/app/`:

- **`app/intelligence/` (5.2)**: Contains status normalizers, freshness checks, and confidence calculations.
- **`app/journey/` (5.3)**: Houses segment filters, safety checks, alternative journey scorers, and ranking pipelines.
- **`app/booking/` (5.4)**: Implements quota check rules, waitlist probability calculators, boarding optimizers, and Tatkal recovery fallback managers.
- **`app/traveler/` (5.5)**: Contains platform drift trackers, connection monitor handlers, and proactive notifications.
- **`app/personalization/` (5.6)**: Houses explicit/implicit preference engines, behavior engines, decay calculations, and consent gates.

---

## 2. Naming Conventions and Module Standards

- **Folder Names**: Lowercase, single words, representing clear domain concepts (e.g. `audit/`, `health/`, `metrics/`, `scenarios/`).
- **Class Naming**: PascalCase matches standard pattern indicators (e.g. `PreferenceEngine`, `PolicyResolver`, `PersonalizationGateway`).
- **Interfaces**: Prefixed with `I` to denote protocols and abstract interfaces (e.g., `IPersonalizationGateway`, `IConfidenceEngine`).

---

## 3. Read/Write Responsibilities and Coupling Boundaries

- **Adapters**: Personalization components connect to prior milestones strictly via read-only adapters, preventing state drift or unintended modifications of core journey/booking layers.
- **Write Paths**: Preference, observation, and audit writing are handled strictly via isolated repositories, protecting data integrity.
- **Transaction Boundaries**: Updates to explicit/implicit profiles are transactional and increment version counts atomically to prevent race conditions during concurrent requests.
