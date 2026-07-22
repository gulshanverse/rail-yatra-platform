"""
Domain Aggregates for Milestone 6.6 AI Response Composer Platform.
Primary aggregate roots enforcing consistency boundaries and business invariants.
"""

from typing import List, Dict, Any, Optional
import time
import uuid

from app.composer.domain.value_objects import (
    ConfidenceMetric,
    ActionChip,
    PolicyCitation,
    ResponseSummary,
    PersonaLayoutMode,
    EmotionalTone,
)
from app.composer.domain.entities import (
    ComposedSection,
    JustificationNode,
    TradeOffChoice,
    TurnSnapshot,
)
from app.composer.domain.events import (
    ComposerDomainEvent,
    ResponseComposedEvent,
    ConflictArbitratedEvent,
    ExplanationGeneratedEvent,
    LowConfidenceWarningEmittedEvent,
)
from app.composer.exceptions import CompositionInvariantViolation


class ResponseComposition:
    """Primary Aggregate Root for Composed Passenger Responses."""

    def __init__(
        self,
        composition_id: Optional[str] = None,
        session_id: str = "",
        traveler_id: str = "",
        layout_mode: PersonaLayoutMode = PersonaLayoutMode.NORMAL,
        emotional_tone: EmotionalTone = EmotionalTone.CALM,
    ):
        self.composition_id = composition_id or str(uuid.uuid4())
        self.session_id = session_id or str(uuid.uuid4())
        self.traveler_id = traveler_id
        self.layout_mode = layout_mode
        self.emotional_tone = emotional_tone

        self.summary: Optional[ResponseSummary] = None
        self.sections: List[ComposedSection] = []
        self.action_chips: List[ActionChip] = []
        self.confidence_metric: Optional[ConfidenceMetric] = None
        self.is_pii_masked: bool = False
        self.created_at: float = time.time()
        self._domain_events: List[ComposerDomainEvent] = []

    def set_summary(self, concise_answer: str) -> None:
        """Sets the lead direct answer summary."""
        self.summary = ResponseSummary(concise_answer=concise_answer)

    def add_section(self, section: ComposedSection) -> None:
        """Adds a structural section element."""
        if not isinstance(section, ComposedSection):
            raise CompositionInvariantViolation("Invalid section instance.")
        self.sections.append(section)

    def add_action_chip(self, chip: ActionChip) -> None:
        """Adds a recommended next-step follow-up chip."""
        if not isinstance(chip, ActionChip):
            raise CompositionInvariantViolation("Invalid action chip instance.")
        if len(self.action_chips) >= 5:
            raise CompositionInvariantViolation("Cannot exceed 5 action chips per response.")
        self.action_chips.append(chip)

    def set_confidence(self, score: float) -> None:
        """Attaches statistical confidence metric."""
        self.confidence_metric = ConfidenceMetric(score=score)

    def validate_invariants(self) -> None:
        """Verifies aggregate boundary invariants."""
        # Invariant 1: Lead answer summary required
        if not self.summary:
            raise CompositionInvariantViolation("BR-RSP-001: ResponseComposition must lead with a concise direct answer summary.")
        # Invariant 2: At least one section required
        if not self.sections:
            raise CompositionInvariantViolation("BR-RSP-002: ResponseComposition must contain at least one content section.")
        # Invariant 3: At least one action chip for multi-turn intent continuation
        if not self.action_chips:
            raise CompositionInvariantViolation("BR-RSP-003: ResponseComposition must contain at least one action guidance chip.")

    def finalize(self, latency_ms: float = 0.0) -> None:
        """Finalizes composition, verifies invariants, and emits ResponseComposedEvent."""
        self.validate_invariants()
        self._record_event(
            ResponseComposedEvent(
                composition_id=self.composition_id,
                session_id=self.session_id,
                traveler_id=self.traveler_id,
                section_count=len(self.sections),
                latency_ms=latency_ms,
            )
        )

    def _record_event(self, event: ComposerDomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[ComposerDomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composition_id": self.composition_id,
            "session_id": self.session_id,
            "traveler_id": self.traveler_id,
            "layout_mode": self.layout_mode.value,
            "emotional_tone": self.emotional_tone.value,
            "summary": self.summary.concise_answer if self.summary else None,
            "sections": [s.to_dict() for s in self.sections],
            "action_chips": [
                {
                    "label": c.label,
                    "intent_payload": c.intent_payload,
                    "is_primary": c.is_primary,
                }
                for c in self.action_chips
            ],
            "confidence_metric": {
                "score": self.confidence_metric.score,
                "certainty_level": self.confidence_metric.certainty_level.value,
            }
            if self.confidence_metric
            else None,
            "is_pii_masked": self.is_pii_masked,
            "created_at": self.created_at,
        }


class ExplanationPayload:
    """Aggregate Root for Multi-Tiered Explainability & Reasoning."""

    def __init__(self, explanation_id: Optional[str] = None, depth_level: int = 1):
        if not (1 <= depth_level <= 4):
            raise CompositionInvariantViolation("Explanation depth_level must be between 1 and 4.")
        self.explanation_id = explanation_id or str(uuid.uuid4())
        self.depth_level = depth_level
        self.justifications: List[JustificationNode] = []
        self.policy_citations: List[PolicyCitation] = []
        self._domain_events: List[ComposerDomainEvent] = []

    def add_justification(self, node: JustificationNode) -> None:
        if not isinstance(node, JustificationNode):
            raise CompositionInvariantViolation("Invalid JustificationNode instance.")
        self.justifications.append(node)

    def add_citation(self, citation: PolicyCitation) -> None:
        if not isinstance(citation, PolicyCitation):
            raise CompositionInvariantViolation("Invalid PolicyCitation instance.")
        self.policy_citations.append(citation)

    def finalize(self) -> None:
        self._record_event(
            ExplanationGeneratedEvent(
                explanation_id=self.explanation_id,
                depth_level=self.depth_level,
                node_count=len(self.justifications),
            )
        )

    def _record_event(self, event: ComposerDomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[ComposerDomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "explanation_id": self.explanation_id,
            "depth_level": self.depth_level,
            "justifications": [j.to_dict() for j in self.justifications],
            "policy_citations": [
                {
                    "clause_number": c.clause_number,
                    "policy_title": c.policy_title,
                    "validity_period": c.validity_period,
                }
                for c in self.policy_citations
            ],
        }


class ConflictArbitration:
    """Aggregate Root for Resolving Multi-Source Model Discrepancies."""

    def __init__(self, arbitration_id: Optional[str] = None):
        self.arbitration_id = arbitration_id or str(uuid.uuid4())
        self.trade_offs: List[TradeOffChoice] = []
        self.resolution_strategy: str = "SAFETY_AND_CERTAINTY_FIRST"
        self.safety_override_active: bool = False
        self._domain_events: List[ComposerDomainEvent] = []

    def add_trade_off(self, choice: TradeOffChoice) -> None:
        if not isinstance(choice, TradeOffChoice):
            raise CompositionInvariantViolation("Invalid TradeOffChoice instance.")
        self.trade_offs.append(choice)

    def resolve(self, chosen_resolution: str, conflicting_sources: List[str]) -> None:
        self._record_event(
            ConflictArbitratedEvent(
                arbitration_id=self.arbitration_id,
                conflicting_sources=conflicting_sources,
                chosen_resolution=chosen_resolution,
            )
        )

    def _record_event(self, event: ComposerDomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[ComposerDomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arbitration_id": self.arbitration_id,
            "resolution_strategy": self.resolution_strategy,
            "safety_override_active": self.safety_override_active,
            "trade_offs": [t.to_dict() for t in self.trade_offs],
        }


class ConversationSession:
    """Aggregate Root for Multi-Turn Session Continuity & Context Inheritance."""

    def __init__(self, session_id: Optional[str] = None, traveler_id: str = ""):
        self.session_id = session_id or str(uuid.uuid4())
        self.traveler_id = traveler_id
        self.turns: List[TurnSnapshot] = []
        self.active_intent: str = "SEARCH_DISCOVERY"
        self.created_at: float = time.time()
        self.last_active_at: float = time.time()

    def add_turn(self, user_input: str, composed_ref: str, intent: str) -> None:
        snapshot = TurnSnapshot(
            user_input=user_input,
            composed_response_ref=composed_ref,
            intent=intent,
            timestamp=time.time(),
        )
        self.turns.append(snapshot)
        self.active_intent = intent
        self.last_active_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "traveler_id": self.traveler_id,
            "turn_count": len(self.turns),
            "active_intent": self.active_intent,
            "turns": [t.to_dict() for t in self.turns],
            "last_active_at": self.last_active_at,
        }


class ConfidenceAssessment:
    """Aggregate Root for Quantitative Prediction Certainty Assessment."""

    def __init__(self, metric: ConfidenceMetric):
        if not isinstance(metric, ConfidenceMetric):
            raise CompositionInvariantViolation("ConfidenceAssessment requires a valid ConfidenceMetric.")
        self.metric = metric
        self.risk_badges: List[str] = []
        self._domain_events: List[ComposerDomainEvent] = []

        # Automatic warning trigger for scores below threshold
        if self.metric.score < 0.60:
            self.risk_badges.append("LOW_CONFIDENCE_CAVEAT")
            self._record_event(
                LowConfidenceWarningEmittedEvent(
                    metric_score=self.metric.score,
                    threshold=0.60,
                    warning_message=f"Prediction certainty is {self.metric.certainty_level.value} ({self.metric.score*100:.0f}%).",
                )
            )

    def _record_event(self, event: ComposerDomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[ComposerDomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.metric.score,
            "certainty_level": self.metric.certainty_level.value,
            "risk_badges": self.risk_badges,
        }
