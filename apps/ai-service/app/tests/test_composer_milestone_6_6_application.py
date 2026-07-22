"""
Automated Test Suite for Milestone 6.6 AI Response Composer Platform — Application Layer & Frameworks.
Verifies Use Cases UC-RSP-01, UC-RSP-02, UC-RSP-03, UC-RSP-04, CQRS, Pipeline Stages, Validators, Formatters,
Prompt Registry, Plugin Architecture, AI Evaluators, Feature Flags, and Telemetry.
"""


from app.composer.application.services import (
    ResponseApplicationService,
    ExplainabilityApplicationService,
    ConversationOrchestrationService,
)
from app.composer.infrastructure.repositories import (
    InMemoryResponseCompositionRepository,
    InMemoryConversationSessionRepository,
    InMemoryComposerAuditLogger,
)
from app.composer.infrastructure.adapters import InMemoryUpstreamIntelligenceAdapter
from app.composer.pipeline.stages import CompositionPipeline
from app.composer.validators.validation import (
    PolicyValidator,
    ConfidenceValidator,
    PrivacyValidator,
)
from app.composer.formatter.formatters import (
    MarkdownFormatter,
    CardFormatter,
    EmergencyFormatter,
    AccessibilityFormatter,
)
from app.composer.prompts.prompt_registry import prompt_registry
from app.composer.plugins.plugin_registry import plugin_registry
from app.composer.evaluation.evaluators import (
    GroundingValidator,
    HallucinationDetector,
    ResponseEvaluator,
)
from app.composer.config import default_composer_config
from app.composer.telemetry import telemetry_collector
from app.composer.feature_flags import feature_flags
from app.composer.domain.aggregates import ResponseComposition, ComposedSection, ActionChip


def test_use_case_uc_rsp_01_compose_journey_plan_response():
    """Verify UC-RSP-01: Compose Journey Plan Response workflow."""
    comp_repo = InMemoryResponseCompositionRepository()
    session_repo = InMemoryConversationSessionRepository()
    audit_logger = InMemoryComposerAuditLogger()
    upstream_port = InMemoryUpstreamIntelligenceAdapter()

    app_svc = ResponseApplicationService(
        composition_repo=comp_repo,
        session_repo=session_repo,
        audit_logger=audit_logger,
        upstream_port=upstream_port,
    )

    traveler_id = "T_SHARMA_67"
    session_id = "SES_1001"

    res = app_svc.compose_journey_response(
        traveler_id=traveler_id,
        session_id=session_id,
        prompt="Trains from Delhi to Pune tomorrow",
    )

    assert res["status"] == "SUCCESS"
    assert "composition_id" in res
    assert res["response"]["summary"] is not None
    assert len(res["response"]["sections"]) >= 1
    assert len(res["response"]["action_chips"]) >= 1

    # Verify retrieval
    retrieved = app_svc.get_composed_response(res["composition_id"])
    assert retrieved["found"] is True


def test_use_case_uc_rsp_02_explain_prediction_odds():
    """Verify UC-RSP-02: Explain Prediction Odds workflow."""
    explain_svc = ExplainabilityApplicationService()

    res = explain_svc.explain_prediction_odds(
        prediction_data={"confidence": 0.78},
        policy_data={"clause": "CL-14", "requires_policy_citation": True},
        confidence_score=0.78,
    )

    assert res["status"] == "SUCCESS"
    assert res["explanation"]["depth_level"] == 4
    assert len(res["explanation"]["policy_citations"]) == 1


def test_use_case_uc_rsp_03_handle_operational_disruption():
    """Verify UC-RSP-03: Handle Operational Disruption conflict arbitration."""
    explain_svc = ExplainabilityApplicationService()

    res = explain_svc.arbitrate_subsystem_conflict(
        planner_option={"train_name": "Train 12626", "duration": "14h"},
        prediction_option={"train_name": "Train 12626", "confirmation_probability": 0.85},
        memory_preference={},
        operational_status={"status": "CANCELLED", "reason": "Route Diversion"},
    )

    assert res["status"] == "SUCCESS"
    assert res["arbitration"]["safety_override_active"] is True


def test_use_case_uc_rsp_04_recover_interrupted_saga():
    """Verify UC-RSP-04: Multi-turn session context retrieval."""
    session_repo = InMemoryConversationSessionRepository()
    conv_svc = ConversationOrchestrationService(session_repo=session_repo)

    res_empty = conv_svc.get_session_context("T_SHARMA_67")
    assert res_empty["has_active_session"] is False


def test_composition_pipeline_13_stages():
    """Verify 13-stage Composition Pipeline execution."""
    pipeline = CompositionPipeline()
    ctx = pipeline.execute(
        traveler_id="T_TEST_1", session_id="SES_99", prompt="Search trains"
    )

    assert ctx.composition is not None
    assert ctx.composition.summary is not None
    assert ctx.quality_result["overall_quality_score"] > 0.5
    assert ctx.latency_ms >= 0.0


def test_validation_framework():
    """Verify independent reusable validators."""
    policy_val = PolicyValidator()
    assert policy_val.validate({}) is True

    conf_val = ConfidenceValidator()
    assert conf_val.validate(0.85) is True

    privacy_val = PrivacyValidator()
    assert privacy_val.validate({"has_consent": True}) is True


def test_presentation_formatters():
    """Verify Presentation Formatter Layer."""
    comp = ResponseComposition()
    comp.set_summary("Rajdhani Express leaves at 16:55.")
    comp.add_section(ComposedSection(content="Platform 3 Departure."))
    comp.add_action_chip(ActionChip(label="Check Seat Odds"))

    md_fmt = MarkdownFormatter()
    md_output = md_fmt.format(comp)
    assert "**Rajdhani Express leaves at 16:55.**" in md_output

    card_fmt = CardFormatter()
    card_output = card_fmt.format(comp)
    assert "summary_card" in card_output

    emerg_fmt = EmergencyFormatter()
    emerg_output = emerg_fmt.format(comp)
    assert "EMERGENCY RAILWAY ADVISORY" in emerg_output

    acc_fmt = AccessibilityFormatter()
    acc_output = acc_fmt.format(comp)
    assert "Rajdhani Express leaves at 16:55." in acc_output


def test_prompt_registry():
    """Verify Prompt Management Framework."""
    prompt_v1 = prompt_registry.get_prompt("COMPOSER_MAIN")
    assert prompt_v1.version_id == "v1.0.0"
    assert "RailYatra AI Response Composer" in prompt_v1.system_prompt


def test_plugin_architecture():
    """Verify Plugin Registry and Metro Connection Plugin."""
    plugin_res = plugin_registry.execute_plugin(
        plugin_name="METRO_CONNECTION_PLUGIN",
        intent="STATION_LAST_MILE",
        payload={"station": "NDLS"},
    )
    assert "Yellow Line Metro" in plugin_res["content"]


def test_ai_evaluators():
    """Verify AI Evaluation Framework."""
    grounding = GroundingValidator.validate_grounding(
        composed_text="Refund terms apply under clause 14.",
        knowledge_items=["clause 14 refund rules"],
    )
    assert grounding["is_grounded"] is True

    hallucination = HallucinationDetector.detect_hallucination(
        composed_text="Guaranteed 100% refund without cancellation fee.",
        verified_facts={"full_refund_allowed": False},
    )
    assert hallucination["hallucination_suspected"] is True

    comp = ResponseComposition()
    comp.set_summary("Rajdhani Express leaves at 16:55.")
    comp.add_section(ComposedSection(content="Platform 3 Departure."))
    comp.add_action_chip(ActionChip(label="Check Seat Odds"))

    eval_res = ResponseEvaluator.evaluate(
        composition=comp, golden_benchmark={"expected_keywords": ["Rajdhani"]}
    )
    assert eval_res["passed"] is True


def test_telemetry_and_feature_flags():
    """Verify Telemetry collector and Feature Flags registry."""
    assert default_composer_config.max_composition_latency_ms == 150.0

    assert feature_flags.is_enabled("DEEP_EVIDENCE_EXPLANATIONS") is True

    telemetry_collector.record_metric("responses_composed_total", 1)
    telemetry_collector.record_span("COMPOSE_RESPONSE", "SES_1", "SUCCESS", 12.5)

    summary = telemetry_collector.get_metrics_summary()
    assert summary["counters"]["responses_composed_total"] == 1
    assert summary["total_spans_recorded"] > 0
