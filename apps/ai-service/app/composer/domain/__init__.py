"""
Domain Layer for Milestone 6.6 AI Response Composer Platform.
Contains value objects, entities, aggregate roots, domain events, specifications, policies,
domain services, and repository ports.
"""

from app.composer.domain.value_objects import (
    CertaintyLevel,
    PersonaLayoutMode,
    InformationPriority,
    EmotionalTone,
    SourceCredibilityRank,
    ConfidenceMetric,
    ActionChip,
    PolicyCitation,
    ResponseSummary,
)
from app.composer.domain.entities import (
    ComposedSection,
    JustificationNode,
    ResolutionFactor,
    TradeOffChoice,
    TurnSnapshot,
)
from app.composer.domain.events import (
    ComposerDomainEvent,
    ResponseComposedEvent,
    ConflictArbitratedEvent,
    ExplanationGeneratedEvent,
    LowConfidenceWarningEmittedEvent,
    PIICompositionMaskedEvent,
    SafetyOverrideTriggeredEvent,
)
from app.composer.domain.aggregates import (
    ResponseComposition,
    ExplanationPayload,
    ConflictArbitration,
    ConversationSession,
    ConfidenceAssessment,
)
from app.composer.domain.specifications import (
    ConsentAwareCompositionSpecification,
    ScannabilitySpecification,
    ConfidenceExplanationRequiredSpecification,
    EmergencyPrioritySpecification,
)
from app.composer.domain.policies import (
    SafetyOverridesConveniencePolicy,
    ConsentGatedPersonalizationPolicy,
    SourceCredibilityPolicy,
    HallucinationPreventionPolicy,
    CommercialNeutralityPolicy,
    PIIMaskingPolicy,
)
from app.composer.domain.services import (
    PrivacyMaskingService,
    ConfidenceCalculationService,
    ArbitrationDomainService,
    ExplainabilityService,
    ResponseSynthesisService,
    ResponseQualityService,
)
from app.composer.domain.repositories import (
    IResponseCompositionRepository,
    IConversationSessionRepository,
    IComposerAuditLogger,
    IUpstreamIntelligencePort,
)

__all__ = [
    "CertaintyLevel",
    "PersonaLayoutMode",
    "InformationPriority",
    "EmotionalTone",
    "SourceCredibilityRank",
    "ConfidenceMetric",
    "ActionChip",
    "PolicyCitation",
    "ResponseSummary",
    "ComposedSection",
    "JustificationNode",
    "ResolutionFactor",
    "TradeOffChoice",
    "TurnSnapshot",
    "ComposerDomainEvent",
    "ResponseComposedEvent",
    "ConflictArbitratedEvent",
    "ExplanationGeneratedEvent",
    "LowConfidenceWarningEmittedEvent",
    "PIICompositionMaskedEvent",
    "SafetyOverrideTriggeredEvent",
    "ResponseComposition",
    "ExplanationPayload",
    "ConflictArbitration",
    "ConversationSession",
    "ConfidenceAssessment",
    "ConsentAwareCompositionSpecification",
    "ScannabilitySpecification",
    "ConfidenceExplanationRequiredSpecification",
    "EmergencyPrioritySpecification",
    "SafetyOverridesConveniencePolicy",
    "ConsentGatedPersonalizationPolicy",
    "SourceCredibilityPolicy",
    "HallucinationPreventionPolicy",
    "CommercialNeutralityPolicy",
    "PIIMaskingPolicy",
    "PrivacyMaskingService",
    "ConfidenceCalculationService",
    "ArbitrationDomainService",
    "ExplainabilityService",
    "ResponseSynthesisService",
    "ResponseQualityService",
    "IResponseCompositionRepository",
    "IConversationSessionRepository",
    "IComposerAuditLogger",
    "IUpstreamIntelligencePort",
]
