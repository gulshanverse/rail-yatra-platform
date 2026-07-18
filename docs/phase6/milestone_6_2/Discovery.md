# Phase 6 - Milestone 6.2 Discovery
## Intent Understanding Engine

---

## 1. Document Control

- **Reference**: RY-P6-M6.2-DISC-1.0
- **Version**: 1.0.0
- **Status**: APPROVED / ACTIVE / FROZEN
- **Authors**: Principal AI Architect, Enterprise Solution Architect
- **Review Authority**: Enterprise Architecture Review Board (ARB)
- **Related Documents**:
  - `Phase6_Engineering_Constitution.md`
  - `Phase6_Roadmap.md`
  - `Milestone_Template.md`
  - `docs/phase6/milestone_6_1/Discovery.md`

---

## 2. Executive Summary
Milestone 6.2 initiates the design and specification of the **Intent Understanding Engine (IUE)**. The IUE serves as the primary cognitive gateway of the RailYatra AI Platform, converting raw, unstructured traveler inputs into structured semantic intents. By decoupling query classification from routing and execution, the IUE provides the foundational intelligence required to govern multi-turn planning and dynamic execution.

---

## 3. Problem Statement
The current conversational platform uses deterministic routing configurations and hardcoded sub-agents to map user prompts. While functional for single-turn dialogs, this approach has key limitations:
- **Tight Semantic Coupling**: The orchestrator must parse context, detect traveler goals, and invoke handlers in a single step, limiting support for complex or multi-intent expressions.
- **Ambiguity Vulnearbility**: Raw user utterances containing spelling variances, missing stations, or vague time references bypass validation gates, causing downstream sub-agent execution failures.
- **Lack of Decoupling**: Adding new specialist agents requires modifying routing rules in the state graph.

---

## 4. Business Drivers
- **Reduced Ambiguity**: Eliminates user frustration by identifying slot gaps (e.g. date missing) early in the pipeline.
- **Optimized Provider Routing**: Accurately classifies user queries to target lower-cost local sub-agents, saving API costs.
- **Multi-Intent Handling**: Prepares the platform to handle compound prompts (e.g., "Check ticket probability and show hotel deals").

---

## 5. Stakeholders
- **End Users**: Receive fast, contextually relevant responses.
- **Orchestrator Node Developers**: Leverage clean structured intent objects.
- **Product Team**: Defines intent families and business rules.
- **Enterprise ARB**: Assures compliance with governance standards.

---

## 6. Current State Analysis
- **Existing Elements**: Gateway facade, State Graph nodes, and base specialist classes.
- **Missing Elements**: Formal semantic classifier layer, slot extraction, confidence scoring, and multi-intent decomposition.
- **Current Limitations**: Prompt classification is coupled with sub-agent workflows.

---

## 7. Desired Future State
After Milestone 6.2, the orchestration pipeline will route requests based on a structured `IntentDescriptor` containing verified intents, slots, and confidence metrics.

---

## 8. Business Objectives
- Increase routing accuracy to over 95%.
- Minimize downstream error rates caused by ambiguous prompts.

---

## 9. Technical Objectives
- Isolate classification from routing.
- Maintain processing latencies below 200ms.

---

## 10. Architectural Objectives
- Enforce strict separation of concerns via Clean Architecture.
- Decouple classifier interfaces from model endpoints.

---

## 11. Scope
- Defining standard intent classification schemas and categories (e.g., booking, status query, general conversation).
- Extracting slot entities (e.g., stations, train numbers, dates).
- Calculating intent confidence scores.
- Standardizing intent context payloads.

---

## 12. Out of Scope
- Downstream Planning Engine execution.
- Tool or external database updates.
- Prompt optimization for specific LLM providers.
- Domain rules (e.g., refund policies).

---

## 13. Functional Requirements
- **Intent Parsing**: Classifies prompts into recognized intent families.
- **Slot Extraction**: Resolves parameters (dates, stations).
- **Confidence Rating**: Assigns probability score.
- **Ambiguity Detection**: Signals downstream nodes if key slots are missing.

---

## 14. Non-Functional Requirements
- **Performance**: Latency < 200ms.
- **Scalability**: Stateless scale-out.
- **Security**: Scrubbing PII data prior to evaluation.
- **Testability**: Isolated mock classifications.

---

## 15. Domain Analysis
- **Intent Family**: High-level semantic action (e.g., `PNR_STATUS`).
- **Intent Category**: Category classification (e.g., transactional, informational).
- **Intent Context**: Variables associated with intent.
- **Intent Confidence**: Decimal score of match likelihood.
- **Ambiguity**: State where slots or target intent families are unclear.

---

## 16. Domain Boundaries
The IUE owns classification and parameter extraction. It does not own execution decisions, memory persistence, or rendering templates.

---

## 17. Context Map
- **Gateway**: Passes message payload to IUE.
- **Capability Registry**: Matches capability metadata against resolved intents.
- **Workflow Policy Engine**: Validates extracted slots against compliance policies.
- **Observability**: Records intent classification metrics and traces.

---

## 18. Risks
- **Over-classification**: Incorrectly classifying conversational prompts as transactional (Mitigation: High confidence gates default to conversation).

---

## 19. Dependencies
- **Milestone 6.1 / 6.1A**: Hardened registry and configurations.
- **Downstream Milestones**: Dynamic planners and tool executors depend on the IUE output.

---

## 20. Assumptions
- User inputs will be raw strings.
- Upstream gateway handles auth and rate limiting.

---

## 21. Constraints
- Must remain database and cloud-provider independent.

---

## 22. Security Considerations
- Context verification to filter out malicious injections or PII.

---

## 23. Observability Considerations
- Event bus triggers for `intent_classified` containing latency, intent family, and confidence metrics.

---

## 24. Architecture Principles
- **Clean Architecture**: Domain core contains zero network or provider library dependencies.
- **SOLID**: Unified interfaces, single responsibilities.

---

## 25. Success Criteria
- **Business**: Zero routing loops.
- **Technical**: Latency within SLAs.
- **Documentation**: Approved and frozen by ARB.

---

## 26. Acceptance Criteria
- Discovery document approved by the ARB.
- Scope limits and interfaces agreed upon by team.

---

## 27. Decision Log

### Decision: Decoupled Parsing
- **Detail**: The classification process will execute in an isolated node prior to routing.
- **Rationale**: Isolates errors and allows fallback configurations.

---

## 28. Future Considerations
- Future integration with multi-intent decomposition and parallel execution paths.

---

## 29. Glossary
- **IUE**: Intent Understanding Engine.
- **Slot**: Entity variable parsed from user message.
- **Intent Descriptor**: Struct containing parsed classification metadata.

---

## 30. Discovery Review Checklist
- [x] No implementation details or code syntax.
- [x] Scope limits defined.
- [x] Architectural boundaries documented.
- [x] approved by review authority.
