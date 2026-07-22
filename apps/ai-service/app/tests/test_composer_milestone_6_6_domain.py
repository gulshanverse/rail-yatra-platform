"""
Automated Test Suite for Milestone 6.6 AI Response Composer Platform — Domain Architecture & DDD.
Verifies Value Objects, Entities, Aggregate Invariants, Domain Events, Specifications, Policies, State Machine,
and Domain Services.
"""

import pytest

from app.composer.domain.value_objects import (
    CertaintyLevel,
    PersonaLayoutMode,
    InformationPriority,
    EmotionalTone,
    ConfidenceMetric,
    ActionChip,
    PolicyCitation,
    ResponseSummary,
)
from app.composer.domain.entities import (
    ComposedSection,
    JustificationNode,
    TradeOffChoice,
)
from app.composer.domain.aggregates import (
    ResponseComposition,
    ExplanationPayload,
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
    PIIMaskingPolicy,
)
from app.composer.domain.services import (
    ArbitrationDomainService,
    ExplainabilityService,
    ResponseQualityService,
)
from app.composer.state_machine import CompositionStateMachine, CompositionState
from app.composer.exceptions import (
    CompositionInvariantViolation,
    IllegalCompositionStateTransition,
)


def test_value_objects_validation():
    """Verify Value Objects immutability and invariant enforcement."""
    metric = ConfidenceMetric(0.92)
    assert metric.score == 0.92
    assert metric.certainty_level == CertaintyLevel.HIGH

    with pytest.raises(CompositionInvariantViolation):
        ConfidenceMetric(1.5)

    chip = ActionChip(label="Book Seat", intent_payload={"action": "BOOK"}, is_primary=True)
    assert chip.label == "Book Seat"

    with pytest.raises(CompositionInvariantViolation):
        ActionChip(label="")

    citation = PolicyCitation(clause_number="CL-14", policy_title="Refund Policy 2026")
    assert citation.clause_number == "CL-14"

    with pytest.raises(CompositionInvariantViolation):
        PolicyCitation(clause_number="", policy_title="")

    summary = ResponseSummary("Train 12951 leaves at 16:55.")
    assert summary.word_count == 5

    with pytest.raises(CompositionInvariantViolation):
        ResponseSummary("")


def test_entities_creation():
    """Verify Entity fields and invariant validations."""
    section = ComposedSection(
        section_type="SUMMARY", content="Direct Rajdhani available.", priority=InformationPriority.PRIMARY
    )
    assert section.content == "Direct Rajdhani available."

    with pytest.raises(CompositionInvariantViolation):
        ComposedSection(content="")

    node = JustificationNode(reasoning_factor="Chart Preparation Window")
    assert node.reasoning_factor == "Chart Preparation Window"

    with pytest.raises(CompositionInvariantViolation):
        JustificationNode(reasoning_factor="")

    trade_off = TradeOffChoice(option_a="Rajdhani", option_b="August Kranti")
    assert trade_off.option_a == "Rajdhani"

    with pytest.raises(CompositionInvariantViolation):
        TradeOffChoice(option_a="", option_b="")


def test_response_composition_aggregate_invariants():
    """Verify ResponseComposition aggregate invariants and domain event emission."""
    comp = ResponseComposition(
        layout_mode=PersonaLayoutMode.NORMAL, emotional_tone=EmotionalTone.CALM
    )

    # Missing summary -> validation fails
    with pytest.raises(CompositionInvariantViolation):
        comp.validate_invariants()

    comp.set_summary("Rajdhani Express leaves at 16:55.")
    comp.add_section(ComposedSection(content="Platform 3 Departure."))
    comp.add_action_chip(ActionChip(label="Check Seat Odds"))
    comp.set_confidence(0.90)

    comp.finalize(latency_ms=45.0)

    events = comp.pop_domain_events()
    assert len(events) == 1
    assert events[0].__class__.__name__ == "ResponseComposedEvent"

    comp_dict = comp.to_dict()
    assert comp_dict["summary"] == "Rajdhani Express leaves at 16:55."
    assert comp_dict["confidence_metric"]["score"] == 0.90


def test_explanation_payload_aggregate():
    """Verify ExplanationPayload aggregate levels and domain events."""
    payload = ExplanationPayload(depth_level=3)
    payload.add_justification(JustificationNode(reasoning_factor="Historical chart trend"))
    payload.finalize()

    events = payload.pop_domain_events()
    assert len(events) == 1
    assert events[0].__class__.__name__ == "ExplanationGeneratedEvent"


def test_confidence_assessment_aggregate():
    """Verify ConfidenceAssessment low confidence warning triggers."""
    low_metric = ConfidenceMetric(0.45)
    assessment = ConfidenceAssessment(metric=low_metric)

    assert "LOW_CONFIDENCE_CAVEAT" in assessment.risk_badges
    events = assessment.pop_domain_events()
    assert len(events) == 1
    assert events[0].__class__.__name__ == "LowConfidenceWarningEmittedEvent"


def test_specifications():
    """Verify Domain Specification Pattern classes."""
    spec_consent = ConsentAwareCompositionSpecification()
    assert spec_consent.is_satisfied_by({"status": "GRANTED"}) is True
    assert spec_consent.is_satisfied_by({"status": "WITHDRAWN"}) is False

    spec_scannable = ScannabilitySpecification()
    comp = ResponseComposition()
    comp.set_summary("Direct answer summary.")
    comp.add_section(ComposedSection(content="Short content"))
    assert spec_scannable.is_satisfied_by(comp) is True

    spec_conf = ConfidenceExplanationRequiredSpecification()
    assert spec_conf.is_satisfied_by(0.75) is True
    assert spec_conf.is_satisfied_by(0.95) is False

    spec_emergency = EmergencyPrioritySpecification()
    assert spec_emergency.is_satisfied_by({"status": "CANCELLED"}) is True
    assert spec_emergency.is_satisfied_by({"status": "ON_TIME"}) is False


def test_domain_policies():
    """Verify Business Policy implementations."""
    # Safety Override Policy
    sections = SafetyOverridesConveniencePolicy.apply_safety_override(
        is_emergency=True,
        emergency_banner="Heavy Fog Delay",
        standard_sections=[{"section_type": "DETAILS", "content": "Schedule info"}],
    )
    assert len(sections) == 2
    assert sections[0]["section_type"] == "WARNING_BANNER"

    # Consent Gated Personalization Policy
    unconsented = ConsentGatedPersonalizationPolicy.filter_preferences(
        has_consent=False, raw_preferences={"berth": "LOWER"}
    )
    assert unconsented == {}

    # PII Masking Policy
    masked_pnr = PIIMaskingPolicy.mask_pii_string("PNR status for 2415678901")
    assert "241****901" in masked_pnr

    masked_name = PIIMaskingPolicy.mask_traveler_name("Mr. Sharma")
    assert "*" in masked_name


def test_composition_state_machine():
    """Verify state machine legal and illegal transitions."""
    sm = CompositionStateMachine()
    assert sm.current_state == CompositionState.INITIATED

    sm.transition_to(CompositionState.CONTEXT_GATHERED)
    sm.transition_to(CompositionState.ARBITRATED)
    sm.transition_to(CompositionState.EXPLAINED)
    sm.transition_to(CompositionState.PRIVACY_CHECKED)
    sm.transition_to(CompositionState.COMPOSED)
    sm.transition_to(CompositionState.VALIDATED)
    sm.transition_to(CompositionState.DELIVERED)

    assert sm.current_state == CompositionState.DELIVERED

    with pytest.raises(IllegalCompositionStateTransition):
        sm.transition_to(CompositionState.INITIATED)


def test_domain_services():
    """Verify Domain Services calculation and quality scoring."""
    # Arbitration Domain Service
    arbitration = ArbitrationDomainService.arbitrate(
        planner_option={"train_name": "Train A", "duration": "12h"},
        prediction_option={"train_name": "Train B", "confirmation_probability": 0.85},
        memory_preference={},
        operational_status={},
    )
    assert len(arbitration.trade_offs) == 1

    # Explainability Service
    explanation = ExplainabilityService.generate_explanation(
        prediction_data={"confidence": 0.70},
        policy_data={"clause": "CL-14", "requires_policy_citation": True},
        confidence_score=0.70,
    )
    assert explanation.depth_level == 4

    # Response Quality Service
    comp = ResponseComposition()
    comp.set_summary("Rajdhani Express leaves at 16:55.")
    comp.add_section(ComposedSection(content="Platform 3 Departure."))
    comp.add_action_chip(ActionChip(label="Check Seat Odds"))
    comp.set_confidence(0.90)

    quality = ResponseQualityService.score_response(comp)
    assert quality["overall_quality_score"] >= 0.80
    assert quality["is_production_ready"] is True
