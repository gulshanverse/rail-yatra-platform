# Milestone 6.3 — Planning & Decision Engine
## Enterprise Implementation Execution Plan (IEP)

---

## 1. Document Control

* **Purpose**: Establish ownership, status, references, and tracing for this implementation execution plan (IEP).
* **Reasoning**: To enforce enterprise governance, accountability, and clear change tracing during the lifecycle of Milestone 6.3.
* **Engineering Decisions**:
  * Document Reference: RY-P6-M6.3-IEP-3.1
  * Version: 3.1.0
  * Status: DRAFT FOR REVIEW
  * Owner: Technical Lead & Principal Backend Architect
  * Governing Documents: `docs/phase6/milestone_6_3/Planning.md` & `docs/phase6/milestone_6_3/Discovery.md`
  * Repository: `gulshanverse/rail-yatra-platform`
* **Dependencies**: Frozen Planning.md and Discovery.md specifications.
* **Acceptance Criteria**: Document is approved by the Technical Design Authority and matches the frozen planning model.
* **Future Evolution**: Version increments will be managed via formal git commits and PR approvals.

---

## 2. Executive Summary

* **Purpose**: Provide a high-level summary of the implementation strategy for the Planning & Decision Engine.
* **Reasoning**: Allows stakeholders to immediately understand the scope, timeline, and engineering approach without reading deep code designs.
* **Engineering Decisions**:
  * Implement a stateless in-memory planning engine in `apps/ai-service/app/planner/`.
  * Create a clean separation between intent parsing (6.2), plan formulation/validation (6.3), and step execution (6.4).
  * Build a 100% covered unit test suite to verify constraints and sequencing.
* **Dependencies**: Intent Understanding Engine pipeline (6.2).
* **Acceptance Criteria**: Verified by successful execution of planning pipeline and 0% regression on previous milestones.
* **Future Evolution**: Prepares for automated executor binding in 6.4.

---

## 3. Implementation Vision

* **Purpose**: Define the engineering vision for the implementation team.
* **Reasoning**: Guides development teams to build clean, maintainable, and decoupled code.
* **Engineering Decisions**:
  * Deliver a modular, type-safe Python 3.11 implementation using Pydantic v2 and clean protocols.
  * Ensure the domain logic remains 100% pure and database-free.
* **Dependencies**: None.
* **Acceptance Criteria**: Compliance with standard ruff, mypy, and pytest tooling.
* **Future Evolution**: Easily portable to microservices or distinct serverless functions.

---

## 4. Implementation Objectives

* **Purpose**: Establish measurable objectives for this engineering phase.
* **Reasoning**: Ensures that the implementation delivers actual business and performance value.
* **Engineering Decisions**:
  * Objective 1: Implement the PlanningCoordinator and ClarificationHandler.
  * Objective 2: Achieve p95 plan formulation latency < 50ms.
  * Objective 3: Maintain 100% test coverage for all specifications and sequencer templates.
* **Dependencies**: Performance strategy (§38) and Testing strategy (§43).
* **Acceptance Criteria**: All performance benchmark tests pass on local and CI/CD runs.
* **Future Evolution**: Objectives can be extended to include memory and prompt caching strategies.

---

## 5. Implementation Scope

* **Purpose**: Bound the features to be coded in this milestone.
* **Reasoning**: Prevents scope creep and ensures on-time delivery of core capabilities.
* **Engineering Decisions**:
  * In Scope: `app/planner/` packages, models, domain services, validator, specifications, policies, factory, and unit tests.
  * Out of Scope: Real database integration, real IRCTC API calls, UI components, actual tool execution engine.
* **Dependencies**: Scope boundaries defined in Planning.md.
* **Acceptance Criteria**: The implemented codebase includes all in-scope modules and none of the out-of-scope targets.
* **Future Evolution**: Out-of-scope elements will be tackled in milestones 6.4 and 6.5.

---

## 6. Implementation Assumptions

* **Purpose**: Define critical deployment and environment preconditions assumed for successful execution.
* **Reasoning**: Explicitly states dependencies external to our direct code control to avoid misalignment.
* **Engineering Decisions**:
  * Assume the intent extraction outputs (`IntentDescriptor`) are normalized and sanitized.
  * Use mocking and standard test fixtures to provide input `IntentDescriptor` values.
* **Dependencies**: Milestone 6.2 IUE.
* **Acceptance Criteria**: The coordinator processes `IntentDescriptor` fixtures correctly.
* **Future Evolution**: Dynamic schema updates will be integrated when 6.2 specifications evolve.

---

## 7. Implementation Constraints

* **Purpose**: Highlight architectural limits and constraints to guide developers.
* **Reasoning**: Prevents structural deviations or unintended performance penalties.
* **Engineering Decisions**:
  * No direct database access or persistent storage writes in `app/planner/`.
  * Pass validation status and results in-memory.
* **Dependencies**: None.
* **Acceptance Criteria**: Linter/code review verifies no database imports or database drivers are used in the planner codebase.
* **Future Evolution**: State management will be handled by Downstream Memory Context in 6.5.

---

## 8. Implementation Strategy

* **Purpose**: Define the high-level roadmap for executing the development.
* **Reasoning**: Optimizes resource usage and minimizes integration errors.
* **Engineering Decisions**:
  * Follow a vertical slice approach: implement data models first, then sequencing, validation specifications, policies, and finally application coordinator and tests.
* **Dependencies**: Development Sequence (§11).
* **Acceptance Criteria**: Code compile checks pass at every stage of the sequence.
* **Future Evolution**: Allows team scaling by assigning individual specifications/policies to different developers.

---

## 9. Engineering Principles

* **Purpose**: Set the standard for coding practices.
* **Reasoning**: Guarantees high-quality, readable, and consistent code.
* **Engineering Decisions**:
  * Adhere to SOLID, DDD, clean protocols, strict type hints, and Pydantic validation.
* **Dependencies**: Ruff, MyPy, and Python configuration.
* **Acceptance Criteria**: Ruff linter, Ruff formatter, and MyPy type checks pass with 0 errors.
* **Future Evolution**: Principles will be shared across all app modules.

---

## 10. Repository Strategy

* **Purpose**: Define file mapping and structural layout in the repository.
* **Reasoning**: Establishes consistency with existing Phase 6 package conventions.
* **Engineering Decisions**:
  * Source root: `apps/ai-service/app/planner/`
  * Layers:
    * Domain: `models.py`, `interfaces.py`, `registry.py`, `specifications.py`, `policies.py`, `events.py`
    * Application: `coordinator.py`, `clarification.py`, `factory.py`, `errors.py`, `sequencer.py`, `validator.py`
    * Test: `apps/ai-service/app/tests/test_planner.py`
* **Dependencies**: Python package import conventions.
* **Acceptance Criteria**: Files are placed exactly in their mapped locations with proper package exports in `__init__.py`.
* **Future Evolution**: Easy packaging of `app/planner` as an independent distribution.

---

## 11. Development Sequence

* **Purpose**: List the sequential steps for implementation.
* **Reasoning**: Minimizes circular dependency blocks during coding.
* **Engineering Decisions**:
  * Step 1: `errors.py` (Base planning exceptions)
  * Step 2: `interfaces.py` (Domain protocols)
  * Step 3: `models.py` (Pydantic aggregates and schemas)
  * Step 4: `registry.py` (Function whitelist)
  * Step 5: `factory.py` (Aggregate factory)
  * Step 6: `events.py` (Event schemas)
  * Step 7: `specifications.py` (Rule specs)
  * Step 8: `policies.py` (Domain policies)
  * Step 9: `sequencer.py` (Sequencer engine)
  * Step 10: `validator.py` (Validation engine)
  * Step 11: `clarification.py` (Clarification orchestrator)
  * Step 12: `coordinator.py` (Coordinator application service)
  * Step 13: `__init__.py` (Exports)
  * Step 14: `tests/test_planner.py` (Pytest suite)
* **Dependencies**: None.
* **Acceptance Criteria**: Every step compile-checks successfully before proceeding to the next.
* **Future Evolution**: Development steps can be integrated into git feature branch PR gates.

---

## 12. Implementation Work Breakdown Structure

* **Purpose**: Translate planning work packages into engineering tasks.
* **Reasoning**: Provides detailed tasks that developers can claim and implement.
* **Engineering Decisions**:
  * Map WP-6.3-01 to WP-6.3-09 to concrete codebase creations.
* **Dependencies**: Work Breakdown Structure (Planning.md §51).
* **Acceptance Criteria**: All planned work packages are accounted for in files.
* **Future Evolution**: WBS can be tracked via Jira/GitHub Issues.

---

## 13. Sprint Planning

* **Purpose**: Schedule tasks into logical execution iterations.
* **Reasoning**: Manages team velocity and delivery timeline.
* **Engineering Decisions**:
  * Iteration 1 (Days 1-2): Code Foundation and Core Models.
  * Iteration 2 (Days 3-4): Code Sequencer, Specifications, and Policies.
  * Iteration 3 (Days 5-6): Code Application Orchestrator, Clarification, and Events.
  * Iteration 4 (Days 7-8): Write Test Suite, Run Audit, Commit.
* **Dependencies**: Resource availability.
* **Acceptance Criteria**: Daily reviews verify progression matches iteration targets.
* **Future Evolution**: Iteration logs are updated in release notes.

---

## 14. Engineering Task Breakdown

* **Purpose**: Detailed list of tasks for the engineer.
* **Reasoning**: Provides step-by-step guidance for code creation.
* **Engineering Decisions**:
  * Task 1: Create `app/planner/errors.py`.
  * Task 2: Create `app/planner/interfaces.py`.
  * Task 3: Create `app/planner/models.py`.
  * Task 4: Create `app/planner/registry.py`.
  * Task 5: Create `app/planner/factory.py`.
  * Task 6: Create `app/planner/events.py`.
  * Task 7: Create `app/planner/specifications.py`.
  * Task 8: Create `app/planner/policies.py`.
  * Task 9: Create `app/planner/sequencer.py`.
  * Task 10: Create `app/planner/validator.py`.
  * Task 11: Create `app/planner/clarification.py`.
  * Task 12: Create `app/planner/coordinator.py`.
  * Task 13: Create `app/planner/__init__.py`.
  * Task 14: Create `app/tests/test_planner.py`.
* **Dependencies**: Development Sequence (§11).
* **Acceptance Criteria**: The developer verifies that the task has been fully implemented according to spec.
* **Future Evolution**: Tasks are updated to "Done" in the local tracking system.

---

## 15. Aggregate Implementation Strategy

* **Purpose**: Describe how the StructuredTravelPlan aggregate root is constructed and validated.
* **Reasoning**: Protects business invariants of the planning aggregate.
* **Engineering Decisions**:
  * Represent `StructuredTravelPlan` as a Pydantic BaseModel.
  * Enforce invariants inside Pydantic model validators:
    * `steps` must be non-empty.
    * `steps` sequence numbers must be unique and ascending.
    * No double bookings (checking passenger IDs and travel times).
* **Dependencies**: `models.py`.
* **Acceptance Criteria**: Creating a plan with invalid sequence numbers or duplicate passenger times throws validation errors.
* **Future Evolution**: Aggregates can support nested transaction logs.

---

## 16. Entity Implementation Strategy

* **Purpose**: Outline the implementation details for the PlanStep entity.
* **Reasoning**: Ensures that individual steps are uniquely identifiable and state-tracked.
* **Engineering Decisions**:
  * Represent `PlanStep` as a BaseModel with a unique `step_id`.
  * Track step inputs, output signatures, status, and prerequisites.
* **Dependencies**: `models.py`.
* **Acceptance Criteria**: Plan steps can transition status through `PlanStepStatus` enums.
* **Future Evolution**: Supports dynamic mapping to execution engine tasks.

---

## 17. Value Object Strategy

* **Purpose**: Describe the implementation details of Constraint and Decision.
* **Reasoning**: Value objects must be immutable and represent values/rules.
* **Engineering Decisions**:
  * Set `frozen=True` on `Constraint` and `Decision` BaseModel configurations to guarantee immutability.
* **Dependencies**: `models.py`.
* **Acceptance Criteria**: Mutating any field on a Constraint or Decision instances throws a TypeError.
* **Future Evolution**: Easy serialization for compliance audits.

---

## 18. Domain Service Strategy

* **Purpose**: Strategy for implementing StepSequencer and PlanValidator.
* **Reasoning**: Separates domain logic from stateful application coordinators.
* **Engineering Decisions**:
  * `StepSequencer` translates intent properties into step lists using predefined templates.
  * `PlanValidator` iterates and evaluates specifications, returning a compiled `ValidationReport`.
* **Dependencies**: `sequencer.py` and `validator.py`.
* **Acceptance Criteria**: Verifies sequencer outputs match specific intent signatures and validator compiles reports.
* **Future Evolution**: Dynamic plugins for custom sequencing templates.

---

## 19. Application Service Strategy

* **Purpose**: Detail the orchestration behavior of PlanningCoordinator and ClarificationHandler.
* **Reasoning**: Coordinates domain actions, handles exceptions, and packages final DTOs.
* **Engineering Decisions**:
  * `PlanningCoordinator` coordinates sequencing, validation, signing, and event publication.
  * `ClarificationHandler` handles missing slot recoveries by creating clarification step prompts.
* **Dependencies**: `coordinator.py` and `clarification.py`.
* **Acceptance Criteria**: The coordinator acts as the single facade for callers, catching internal domain exceptions.
* **Future Evolution**: Interfacing with the conversation history registry.

---

## 20. Specification Implementation Strategy

* **Purpose**: Strategy for coding AgeEligibleSpecification, TimeWindowSpecification, and DoubleBookingSpecification.
* **Reasoning**: Ensures clean, isolated rule evaluations following the Specification Pattern.
* **Engineering Decisions**:
  * Implement base class with `is_satisfied_by(plan)`.
  * Evaluate conditions based on plan passenger age, time layovers, and overlapping schedules.
* **Dependencies**: `specifications.py`.
* **Acceptance Criteria**: Tests verify correct failure responses for passengers under age limit, layovers < 45m, and matching travel times.
* **Future Evolution**: Support boolean composition operators (AND, OR, NOT).

---

## 21. Policy Implementation Strategy

* **Purpose**: Strategy for LockoutPolicy, IdentitySafetyPolicy, and ConcessionValidationPolicy.
* **Reasoning**: Enforces high-level platform guardrails.
* **Engineering Decisions**:
  * Models evaluate against incoming user request contexts.
  * `LockoutPolicy` blocks bookings within chart preparation (4h).
* **Dependencies**: `policies.py`.
* **Acceptance Criteria**: Policies correctly return validation flags when conditions are violated.
* **Future Evolution**: Shared policy register loaded from external configuration servers.

---

## 22. Factory Strategy

* **Purpose**: Strategy for StructuredTravelPlanFactory.
* **Reasoning**: Decouples plan construction complexity from application services.
* **Engineering Decisions**:
  * Factory generates UUIDs, sets initial `status = DRAFT`, and links trace IDs.
* **Dependencies**: `factory.py`.
* **Acceptance Criteria**: Factories return well-formed plans with generated UUIDs and valid structures.
* **Future Evolution**: Support plan cloning and version branching.

---

## 23. Repository Strategy

* **Purpose**: Define database/persistence interactions for the planner.
* **Reasoning**: The engine is designed to be stateless (ADR-M6.3-002).
* **Engineering Decisions**:
  * Do not implement database access in the planner.
  * Return signed, validated plan outputs directly.
* **Dependencies**: None.
* **Acceptance Criteria**: Code contains 0 persistence operations.
* **Future Evolution**: Downstream services will serialize plans into redis/session storage.

---

## 24. Dependency Injection Strategy

* **Purpose**: Map how dependencies are injected.
* **Reasoning**: Prevents tight coupling and simplifies unit testing via mocks.
* **Engineering Decisions**:
  * Inject `IStepSequencer` and `IPlanValidator` implementations into the `PlanningCoordinator` constructor.
* **Dependencies**: `interfaces.py`.
* **Acceptance Criteria**: Coordinator can be instantiated with mocked sequencers and validators in test cases.
* **Future Evolution**: Integration with standard DI frameworks (e.g., fastinject or simple container scripts).

---

## 25. Configuration Strategy

* **Purpose**: Outline the storage and loading of thresholds.
* **Reasoning**: Allows tweaking layover times or age limits without redeploying code.
* **Engineering Decisions**:
  * Read parameters from a centralized config object matching `platform_config`.
* **Dependencies**: `config.py`.
* **Acceptance Criteria**: Changing configuration values changes validator behaviors dynamically.
* **Future Evolution**: Dynamic configuration hot-reload capability.

---

## 26. Error Handling Strategy

* **Purpose**: Strategy for catching, wrapping, and reporting planning errors.
* **Reasoning**: Prevents raw tracebacks from leaking to users and provides clear validation reports.
* **Engineering Decisions**:
  * Catch domain invariants inside application layer, translate to appropriate exception types, and log with traceback context.
* **Dependencies**: `errors.py`.
* **Acceptance Criteria**: Raising validation errors is correctly captured by the coordinator and populated in error lists.
* **Future Evolution**: Integration with centralized error trackers (Sentry, etc.).

---

## 27. Exception Hierarchy

* **Purpose**: List custom planning exception types.
* **Reasoning**: Standardizes error handling and reporting.
* **Engineering Decisions**:
  * `PlanningError` (Base class)
  * `ValidationError` (Constraint violations)
  * `SequencingError` (Step dependencies missing)
  * `UnauthorizedFunctionError` (Function whitelist mismatch)
  * `ClarificationRequiredError` (Missing slots)
  * `PolicyViolationError` (Domain policy blocks)
* **Dependencies**: `errors.py`.
* **Acceptance Criteria**: Custom exceptions inherit from `PlanningError` and print formatted error details.
* **Future Evolution**: Errors mapped to specific HTTP status codes in gateway interfaces.

---

## 28. Validation Strategy

* **Purpose**: Define validation pipeline execution order.
* **Reasoning**: Ensures all rules are checked systematically.
* **Engineering Decisions**:
  * Run validation in three steps:
    1. Schema validation (Pydantic parsing)
    2. Policy check (Lockout, Identity)
    3. Constraint check (Specifications: Age, Time, Booking overlap)
* **Dependencies**: `validator.py`, `specifications.py`, `policies.py`.
* **Acceptance Criteria**: Plan validator catches validation failures at any phase and formats them in the output report.
* **Future Evolution**: Fail-fast configuration option.

---

## 29. Business Rule Strategy

* **Purpose**: Maintain railway regulations.
* **Reasoning**: Ensures business compliance with railway authority regulations.
* **Engineering Decisions**:
  * Rule configurations are loaded from JSON files, mapping age thresholds and layout parameters.
* **Dependencies**: `config.py`.
* **Acceptance Criteria**: Changing local rules files updates verification checks.
* **Future Evolution**: Remote compliance update feed.

---

## 30. AI Integration Strategy

* **Purpose**: Define AI reasoning integration inside the planning engine.
* **Reasoning**: Planning logic wraps model classifications with safe, deterministic rules.
* **Engineering Decisions**:
  * Accept classification outputs from 6.2 and construct templates.
  * Do not make direct LLM calls during plan sequencing.
* **Dependencies**: None.
* **Acceptance Criteria**: Sequence templates are generated purely deterministically based on parsed slots.
* **Future Evolution**: LLM-based plan repair logic.

---

## 31. Prompt Integration Strategy

* **Purpose**: Outline prompt usage.
* **Reasoning**: The planner is deterministic and does not use conversational prompts directly (delegated to 6.2 and 6.6).
* **Engineering Decisions**:
  * No prompt templates are stored in `app/planner/`.
* **Dependencies**: None.
* **Acceptance Criteria**: Absence of prompt configurations in planner modules.
* **Future Evolution**: Prompts for plan repair generation.

---

## 32. Memory Integration Strategy

* **Purpose**: Define state restoration approach.
* **Reasoning**: The planner remains stateless; caller must pass context.
* **Engineering Decisions**:
  * Accept traveler history context as dictionary parameter in coordinator calls.
* **Dependencies**: None.
* **Acceptance Criteria**: Coordinator applies traveler details from context during concession and double-booking evaluations.
* **Future Evolution**: Automated state retrieval from Memory service in 6.5.

---

## 33. Tool Integration Strategy

* **Purpose**: Whitelist and register execution tools.
* **Reasoning**: Ensures the planner only sequences tools that actually exist in the platform capability.
* **Engineering Decisions**:
  * Match step names to whitelisted keys in `ApprovedFunctionRegistry`.
* **Dependencies**: `registry.py`.
* **Acceptance Criteria**: Planning steps that reference unapproved function names are rejected.
* **Future Evolution**: Automated capability discovery via service annotations.

---

## 34. Observability Implementation

* **Purpose**: Provide execution pipeline visibility.
* **Reasoning**: Enables tracking system metrics and performance trends.
* **Engineering Decisions**:
  * Instrument planning workflow with structured timing metrics and correlation logs.
* **Dependencies**: Python standard logging.
* **Acceptance Criteria**: Tracing runs verify duration and performance across code gates.
* **Future Evolution**: Integration with OpenTelemetry.

---

## 35. Logging Strategy

* **Purpose**: Setup logging patterns.
* **Reasoning**: Provides debug information during issue diagnostics.
* **Engineering Decisions**:
  * Use standardized log names: `ai-service.planner.coordinator`, `ai-service.planner.sequencer`, etc.
  * Mask PII fields prior to writing to logs.
* **Dependencies**: Logger configurations.
* **Acceptance Criteria**: Log checks confirm absence of passenger details in outputs.
* **Future Evolution**: Shipping to centralized log systems.

---

## 36. Tracing Strategy

* **Purpose**: Track planning transactions.
* **Reasoning**: Links planning events to the originating request.
* **Engineering Decisions**:
  * Carry `trace_id` from intent metadata into planning models and logs.
* **Dependencies**: `models.py`.
* **Acceptance Criteria**: All logged messages and events include the trace ID.
* **Future Evolution**: Integration with Jaeger tracing.

---

## 37. Metrics Strategy

* **Purpose**: Measure operational KPI indicators.
* **Reasoning**: Monitors engine effectiveness and performance.
* **Engineering Decisions**:
  * Track:
    * `planning_request_count` (total requests)
    * `planning_validation_failures` (violations rate)
    * `planning_duration_ms` (latency metrics)
* **Dependencies**: None.
* **Acceptance Criteria**: Latency timers log start and finish times for every transaction.
* **Future Evolution**: Exporting metrics to Prometheus/Grafana.

---

## 38. Performance Strategy

* **Purpose**: Minimize system overhead.
* **Reasoning**: Prevents planning engine latency from delaying user replies.
* **Engineering Decisions**:
  * Avoid expensive regex loops inside validation; check pre-compiled patterns and simple lookups.
* **Dependencies**: None.
* **Acceptance Criteria**: Benchmarks confirm average processing time per plan is < 15ms.
* **Future Evolution**: Caching common plan templates in redis.

---

## 39. Scalability Strategy

* **Purpose**: Strategy for high traffic loads.
* **Reasoning**: Ensures platform remains responsive under load.
* **Engineering Decisions**:
  * Complete stateless architecture means any thread/worker can process any request.
* **Dependencies**: None.
* **Acceptance Criteria**: Concurrency checks verify error-free parallel execution across threads.
* **Future Evolution**: Deployment onto autoscale container nodes.

---

## 40. Security Implementation Strategy

* **Purpose**: Prevent plan manipulation.
* **Reasoning**: Protects platform from malicious prompt inject attempts.
* **Engineering Decisions**:
  * Run validation constraints over every generated plan step, rejecting unrecognized schemas and function signatures.
* **Dependencies**: `registry.py`, `validator.py`.
* **Acceptance Criteria**: Plans containing unapproved step attributes fail validation.
* **Future Evolution**: Integration with security scanners.

---

## 41. Privacy Implementation Strategy

* **Purpose**: Sanitize passenger details.
* **Reasoning**: Ensures compliance with DPDP act and data privacy guidelines.
* **Engineering Decisions**:
  * Redact or mock-encrypt traveler credentials prior to writing log statements.
* **Dependencies**: `normalizer.py` (M6.2).
* **Acceptance Criteria**: Log files contain zero plain-text customer personal data.
* **Future Evolution**: Dynamic field masking utilities.

---

## 42. Compliance Implementation Strategy

* **Purpose**: Maintain regulatory rules.
* **Reasoning**: Ensures all validation rules meet official guidelines.
* **Engineering Decisions**:
  * Audit check runs monthly review comparing coded specifications to IR regulations.
* **Dependencies**: `specifications.py`.
* **Acceptance Criteria**: Audit results document version compliance status.
* **Future Evolution**: Automated compliance scans.

---

## 43. Testing Philosophy

* **Purpose**: Set testing expectations.
* **Reasoning**: Guarantees system stability and zero regressions.
* **Engineering Decisions**:
  * Write clean, isolated tests for every file in `app/planner/`.
  * Ensure 100% test coverage.
* **Dependencies**: PyTest framework.
* **Acceptance Criteria**: Pytest suite runs green for all new files.
* **Future Evolution**: Integration in git pull request pre-commit hooks.

---

## 44. Unit Testing Strategy

* **Purpose**: Verify individual classes.
* **Reasoning**: Checks correct behavior of small functional blocks in isolation.
* **Engineering Decisions**:
  * Write tests for:
    * `test_models.py` (invariants, parsing)
    * `test_sequencer.py` (templates, step ordering)
    * `test_specifications.py` (age, layover, overlap checks)
    * `test_validator.py` (report generation)
* **Dependencies**: `tests/test_planner.py`.
* **Acceptance Criteria**: Individual unit test assertions evaluate to true.
* **Future Evolution**: Fast-running unit test suites.

---

## 45. Integration Testing Strategy

* **Purpose**: Verify pipeline interactions.
* **Reasoning**: Checks that modules work together seamlessly.
* **Engineering Decisions**:
  * Run end-to-end tests calling the `PlanningCoordinator` with sample inputs and verifying final plan outputs.
* **Dependencies**: `coordinator.py`.
* **Acceptance Criteria**: The end-to-end flow correctly routes to clarification or validation.
* **Future Evolution**: Testing integration with downstream executor mock adapters.

---

## 46. Architecture Testing Strategy

* **Purpose**: Verify structural bounds.
* **Reasoning**: Prevents developers from introducing circular or invalid dependencies.
* **Engineering Decisions**:
  * Use code structure tests to check imports and confirm no database wrappers are imported in `app/planner/`.
* **Dependencies**: None.
* **Acceptance Criteria**: Structure test checks pass.
* **Future Evolution**: Integration of ArchUnit-style testing tools.

---

## 47. Regression Testing Strategy

* **Purpose**: Prevent breaking existing features.
* **Reasoning**: Ensures that new code does not break intent parsing (6.2) or search APIs.
* **Engineering Decisions**:
  * Execute the entire pytest suite for the project.
* **Dependencies**: Existing pytest suite (298 tests).
* **Acceptance Criteria**: All 298 tests continue to pass with 0 failures.
* **Future Evolution**: Automated nightly regression runs.

---

## 48. Acceptance Testing Strategy

* **Purpose**: Map verification to discovery requirements.
* **Reasoning**: Confirms business objectives have been successfully achieved.
* **Engineering Decisions**:
  * Test scenarios matching प्रिया (Priya) and राज (Raj) journey flows from Discovery.
* **Dependencies**: Discovery Personas (§8).
* **Acceptance Criteria**: Priya's senior concession is validation checked, and Raj's alternative routes are generated.
* **Future Evolution**: Automated customer scenario tests.

---

## 50. Security Testing Strategy

* **Purpose**: Verify injection resilience.
* **Reasoning**: Checks that invalid tool calls or parameter manipulation attempts are blocked.
* **Engineering Decisions**:
  * Test sending plans containing unknown function names or malformed inputs and verify rejection.
* **Dependencies**: `test_planner.py`.
* **Acceptance Criteria**: Registry and validator block all invalid requests.
* **Future Evolution**: Automated security vulnerability scanning.

---

## 49. Performance Testing Strategy

* **Purpose**: Validate responsiveness.
* **Reasoning**: Verifies engine processing speeds meet constraints under load.
* **Engineering Decisions**:
  * Code benchmarking tests running 1000 planning cycles in parallel and reporting time averages.
* **Dependencies**: Pytest-benchmark or simple timing wrappers.
* **Acceptance Criteria**: Average transaction time remains < 15ms.
* **Future Evolution**: Continuous profiling dashboard.

---

## 51. Implementation Quality Gates

* **Purpose**: Set gates that must pass before merging code.
* **Reasoning**: Prevents bad code from reaching main branch.
* **Engineering Decisions**:
  * Ruff linter: 0 warnings
  * Ruff formatter check: pass
  * MyPy typings: 0 errors
  * Pytest test suite: 100% green
  * Test coverage: 100% for `app/planner/`
* **Dependencies**: GitHub actions or local pre-commit checks.
* **Acceptance Criteria**: All quality gates show green status.
* **Future Evolution**: Automatic release builds triggering after gates pass.

---

## 52. Implementation Review Checklist

* **Purpose**: Verify code conforms to specifications.
* **Reasoning**: Double-checks quality before release.
* **Engineering Decisions**:
  * Use a structured reviewer list:
    * Are aggregate invariants enforced?
    * Do all specifications check correct boundaries?
    * Is there any database leakage?
* **Dependencies**: None.
* **Acceptance Criteria**: Review checklist is completed and signed off.
* **Future Evolution**: Integration into PR description templates.

---

## 53. Code Review Checklist

* **Purpose**: Detailed checklist for developers reviewing code.
* **Reasoning**: Catches bugs and design issues early.
* **Engineering Decisions**:
  * Review checklist items:
    * Check type hints on all function signatures.
    * Check Pydantic model configurations (frozen=True for VOs).
    * Verify exception wrapping in the coordinator.
* **Dependencies**: Code review tool.
* **Acceptance Criteria**: PR approved by at least one architect.
* **Future Evolution**: Automated code review assistance.

---

## 54. Definition of Done

* **Purpose**: Define clear criteria for task completion.
* **Reasoning**: Ensures all engineering artifacts are complete before feature is marked done.
* **Engineering Decisions**:
  * DoD criteria:
    * All code is written and compile-checked.
    * Unit and integration tests are written and run green.
    * Coverage is 100%.
    * Ruff lint and MyPy type checks pass.
    * Documentation (technical walkthrough, implementation report, audit report) is generated.
* **Dependencies**: None.
* **Acceptance Criteria**: All tasks meet DoD criteria before branch is merged.
* **Future Evolution**: Automated DoD verification scripts.

---

## 55. Implementation Risks

* **Purpose**: Identify engineering risks during coding.
* **Reasoning**: Prevents development bottlenecks and unexpected delays.
* **Engineering Decisions**:
  * Risk 1: Performance impact of deep validation checks.
  * Risk 2: Schema mismatch between 6.2 intent output and 6.3 input.
* **Dependencies**: Risk Register (Planning.md §49).
* **Acceptance Criteria**: Risks are documented and tracking mitigations is active.
* **Future Evolution**: Risk logs updated in project retrospective.

---

## 56. Mitigation Plan

* **Purpose**: Define mitigation steps for risks.
* **Reasoning**: Minimizes the impact of risks if they occur.
* **Engineering Decisions**:
  * Mitigation 1: Keep validation rules local and compile patterns once at startup.
  * Mitigation 2: Share and synchronize `IntentDescriptor` Pydantic models between modules.
* **Dependencies**: Implementation Risks (§55).
* **Acceptance Criteria**: Mitigations are implemented in code.
* **Future Evolution**: Updating mitigations based on testing findings.

---

## 57. Rollback Strategy

* **Purpose**: Revert code changes safely if errors occur in staging.
* **Reasoning**: Protects platform branch integrity.
* **Engineering Decisions**:
  * Use git revert to safely undo the merge commit.
  * Ensure the code reverts cleanly to the Milestone 6.2 commit tag without leaving orphaned changes.
* **Dependencies**: Git history.
* **Acceptance Criteria**: Reverting the merge restores codebase to M6.2 state and runs existing test suite successfully.
* **Future Evolution**: Automated deployment rollback pipelines.

---

## 58. Deployment Readiness

* **Purpose**: Verify pre-requisites for deployment.
* **Reasoning**: Ensures smooth release to staging.
* **Engineering Decisions**:
  * Check dependencies, configuration files, and test coverage before merging.
* **Dependencies**: Quality Gates (§51).
* **Acceptance Criteria**: All readiness checklist items are marked off.
* **Future Evolution**: Auto-deployment pipeline scripts.

---

## 59. Implementation Audit Checklist

* **Purpose**: Verify architecture compliance of the implementation.
* **Reasoning**: Confirms developer did not drift from the frozen architecture.
* **Engineering Decisions**:
  * Audit verification:
    * Did the developer implement the exact aggregate root name (`StructuredTravelPlan`)?
    * Are all whitelisted functions defined in the registry?
    * Is there any database leakage?
* **Dependencies**: Audit Report Template (Milestone_Template.md §9).
* **Acceptance Criteria**: Audit results document 100% compliance with Planning.md.
* **Future Evolution**: Automated architecture compliance checks.

---

## 60. Implementation Readiness Assessment

* **Purpose**: Final maturity score before coding starts.
* **Reasoning**: Confirms the plan is complete enough for development to proceed.
* **Engineering Decisions**:
  * Readiness score: **9.8 / 10** (Outstanding)
  * Rationale: Full model mappings, clean protocol abstractions, and detailed sequence schedules are provided.
* **Dependencies**: None.
* **Acceptance Criteria**: Technical Lead approves transition to coding.
* **Future Evolution**: Dashboard for readiness metrics.

---

## 61. Implementation Freeze

* **Purpose**: Lock the implementation plan before development starts.
* **Reasoning**: Prevents design churn during coding.
* **Engineering Decisions**:
  * Freeze Date: 2026-07-21
  * Version: 3.1.0
  * Approvers: Lead Architect, Backend Lead
* **Dependencies**: Final Approval (§63).
* **Acceptance Criteria**: IEP file is marked as FROZEN and committed to git.
* **Future Evolution**: Changes to the plan require a formal change request.

---

## 62. Transition to Development

* **Purpose**: Direct transition of code creation.
* **Reasoning**: Initiates the physical coding phase.
* **Engineering Decisions**:
  * Technical Lead authorizes developer to begin coding Task 1 through Task 14.
* **Dependencies**: Implementation Freeze (§61).
* **Acceptance Criteria**: The developer starts coding foundation files.
* **Future Evolution**: Development logs are tracked in pull request history.

---

## 63. Final Approval

* **Purpose**: Record formal sign-off for the execution plan.
* **Reasoning**: Enforces corporate quality governance.
* **Engineering Decisions**:
  * Approved by: Enterprise Solution Architect & Technical Design Authority
  * Date: 2026-07-21
  * Status: APPROVED
* **Dependencies**: All preceding sections.
* **Acceptance Criteria**: Technical Design Authority signs off on the IEP version.
* **Future Evolution**: Artifact archived in milestone release logs.
