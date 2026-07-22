"""
Structured Response Contracts for Milestone 6.6 AI Response Composer Platform.
Strongly typed contracts defining universal JSON schemas for API responses, recommendations,
evidence, confidence, explanations, warnings, and action chips.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SourceAttributionContract:
    """Contract for data source attribution and grounding."""

    source_name: str
    source_type: str  # OPERATIONAL_API, POLICY_DOCUMENT, PREDICTION_MODEL, TRAVELER_MEMORY
    credibility_rank: int
    reference_id: Optional[str] = None


@dataclass
class EvidenceContract:
    """Contract for evidence items supporting recommendations."""

    evidence_id: str
    reasoning_factor: str
    attribution: SourceAttributionContract
    data_points: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReasoningContract:
    """Contract for multi-tiered reasoning payloads."""

    depth_level: int
    evidence_chain: List[EvidenceContract] = field(default_factory=list)
    summary_takeaway: str = ""


@dataclass
class PolicyCitationContract:
    """Contract for official IRCTC / Railway Board citations."""

    clause_number: str
    policy_title: str
    validity_period: str


@dataclass
class ExplanationContract:
    """Contract for complete explainability payloads."""

    explanation_id: str
    reasoning: ReasoningContract
    citations: List[PolicyCitationContract] = field(default_factory=list)


@dataclass
class ConfidenceContract:
    """Contract for statistical confidence scores and risk caveats."""

    score: float
    certainty_level: str  # HIGH, MEDIUM, LOW, UNCERTAIN
    risk_badges: List[str] = field(default_factory=list)


@dataclass
class WarningContract:
    """Contract for operational disruption and emergency warning banners."""

    warning_type: str  # DELAY, CANCELLATION, DIVERSION, WEATHER
    message: str
    urgency: str  # EMERGENCY, CRITICAL, ADVISORY


@dataclass
class ActionContract:
    """Contract for interactive action guidance chips."""

    label: str
    intent: str
    payload: Dict[str, Any] = field(default_factory=dict)
    is_primary: bool = False


@dataclass
class ClarificationContract:
    """Contract for resolving ambiguous passenger prompts."""

    ambiguous_term: str
    suggested_interpretations: List[str]
    clarification_prompt: str


@dataclass
class SuggestionContract:
    """Contract for proactive follow-up recommendations."""

    title: str
    description: str
    action_chip: ActionContract


@dataclass
class RecommendationContract:
    """Contract for individual train, seat, or route recommendations."""

    recommendation_id: str
    title: str
    subtitle: str
    rank: int
    trade_off_summary: Optional[str] = None
    confidence: Optional[ConfidenceContract] = None
    action: Optional[ActionContract] = None


@dataclass
class MetadataContract:
    """Contract for response composition metadata and telemetry."""

    composition_id: str
    session_id: str
    traveler_id: str
    latency_ms: float
    is_pii_masked: bool
    quality_score: float
    timestamp: float


@dataclass
class ComposedResponseContract:
    """Primary Strongly Typed Contract for the AI Response Composer Platform."""

    summary_answer: str
    sections: List[Dict[str, Any]]
    recommendations: List[RecommendationContract] = field(default_factory=list)
    explanation: Optional[ExplanationContract] = None
    confidence: Optional[ConfidenceContract] = None
    warnings: List[WarningContract] = field(default_factory=list)
    actions: List[ActionContract] = field(default_factory=list)
    clarification: Optional[ClarificationContract] = None
    suggestions: List[SuggestionContract] = field(default_factory=list)
    metadata: Optional[MetadataContract] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary_answer": self.summary_answer,
            "sections": self.sections,
            "recommendations": [
                {
                    "id": r.recommendation_id,
                    "title": r.title,
                    "subtitle": r.subtitle,
                    "rank": r.rank,
                    "trade_off": r.trade_off_summary,
                }
                for r in self.recommendations
            ],
            "confidence": {
                "score": self.confidence.score,
                "level": self.confidence.certainty_level,
                "badges": self.confidence.risk_badges,
            }
            if self.confidence
            else None,
            "warnings": [
                {"type": w.warning_type, "message": w.message, "urgency": w.urgency}
                for w in self.warnings
            ],
            "actions": [
                {
                    "label": a.label,
                    "intent": a.intent,
                    "payload": a.payload,
                    "is_primary": a.is_primary,
                }
                for a in self.actions
            ],
            "metadata": {
                "composition_id": self.metadata.composition_id,
                "session_id": self.metadata.session_id,
                "latency_ms": self.metadata.latency_ms,
                "quality_score": self.metadata.quality_score,
            }
            if self.metadata
            else None,
        }
