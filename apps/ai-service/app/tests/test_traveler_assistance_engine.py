# app/tests/test_traveler_assistance_engine.py
"""
Comprehensive test suite for Milestone 5.5 – Traveler Assistance & Proactive
Intelligence Platform.

Test categories (Planning §16):
  - Unit tests:        Context factory validations, engine isolation checks
  - Integration tests: Full pipeline orchestration through the gateway
  - Scenario tests:    Cancellation, platform swap, missed transfer, medical
  - Boundary tests:    GDS import leak prevention, error taxonomy checks
"""

import ast
import os
import unittest
import asyncio
from app.traveler.gateway.coordinator import (
    TravelerDecisionContextFactory,
    TravelerCoordinator,
    TravelerAssistanceGateway,
)
from app.traveler.pipeline.orchestrator import TravelerPipelineOrchestrator
from app.traveler.timeline.engine import TimelineEngine
from app.traveler.timeline.checkpoint import CheckpointEngine
from app.traveler.alerts.alert_engine import AlertEngine
from app.traveler.alerts.reminder_engine import ReminderEngine
from app.traveler.alerts.guidance_engine import GuidanceEngine
from app.traveler.strategy.recovery_engine import RecoveryEngine
from app.traveler.strategy.action_engine import (
    ActionEngine,
    TravelerStrategyRegistry,
    SafetyFirstStrategy,
    MedicalTravelerStrategy,
)
from app.traveler.strategy.scenario_registry import (
    ScenarioRegistry,
    PlatformChangedScenario,
    TrainCancelledScenario,
    MedicalEmergencyScenario,
    WheelchairTravelerScenario,
)
from app.traveler.risk.risk_engine import RiskEngine
from app.traveler.risk.confidence_engine import ConfidenceEngine
from app.traveler.risk.priority import (
    PriorityEngine,
    SuppressionEngine,
    EscalationEngine,
)
from app.traveler.policy.resolver import PolicyResolver
from app.traveler.explanation.engine import ExplanationEngine
from app.traveler.events.event_engine import EventEngine
from app.traveler.events.publisher import TravelerEventPublisher
from app.traveler.cache.manager import TravelerCacheManager
from app.traveler.audit.logger import AuditEngine
from app.traveler.metrics.collector import MetricsEngine
from app.traveler.health.checker import HealthEngine
from app.traveler.config.registry import is_feature_enabled, get_policy
from app.traveler.errors import (
    TravelerError,
    ContextError,
    TimelineError,
    CheckpointError,
    AlertError,
    RecoveryError,
    ExplanationError,
    PolicyError,
)


def _run(coro):
    """Helper – run an async coroutine synchronously."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _make_telemetry(**overrides):
    """Build a valid telemetry dict with sensible defaults."""
    base = {
        "traveler_id": "usr_99",
        "journey_id": "jrn_100",
        "booking_id": "pnr_100",
        "drift_minutes": 0.0,
    }
    base.update(overrides)
    return base


def _build_gateway():
    """Wire up a fully-functional gateway for integration tests."""
    orchestrator = TravelerPipelineOrchestrator(
        timeline_engine=TimelineEngine(),
        alert_engine=AlertEngine(),
        reminder_engine=ReminderEngine(),
        action_engine=ActionEngine(),
        recovery_engine=RecoveryEngine(),
        explanation_engine=ExplanationEngine(),
        confidence_engine=ConfidenceEngine(),
    )
    coordinator = TravelerCoordinator(
        orchestrator=orchestrator,
        audit_engine=AuditEngine(),
        metrics_engine=MetricsEngine(),
        event_publisher=TravelerEventPublisher(),
    )
    return TravelerAssistanceGateway(coordinator=coordinator)


# ===================================================================
# 1. UNIT TESTS
# ===================================================================


class TestContextFactory(unittest.TestCase):
    """Validates TravelerDecisionContextFactory input checks."""

    def test_missing_traveler_id_raises(self):
        with self.assertRaises(ValueError):
            TravelerDecisionContextFactory.create_context(
                {"journey_id": "j1", "booking_id": "b1"}, "corr-001"
            )

    def test_missing_journey_id_raises(self):
        with self.assertRaises(ValueError):
            TravelerDecisionContextFactory.create_context(
                {"traveler_id": "u1", "booking_id": "b1"}, "corr-002"
            )

    def test_missing_booking_id_raises(self):
        with self.assertRaises(ValueError):
            TravelerDecisionContextFactory.create_context(
                {"traveler_id": "u1", "journey_id": "j1"}, "corr-003"
            )

    def test_empty_correlation_id_raises(self):
        with self.assertRaises(ValueError):
            TravelerDecisionContextFactory.create_context(_make_telemetry(), "")

    def test_valid_context_fields(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(), "corr-ok"
        )
        self.assertEqual(ctx.traveler_id, "usr_99")
        self.assertEqual(ctx.journey_id, "jrn_100")
        self.assertEqual(ctx.booking_id, "pnr_100")
        self.assertEqual(ctx.correlation_id, "corr-ok")
        self.assertEqual(ctx.active_state, "PRE_DEPARTURE")
        self.assertEqual(ctx.status, "PUNCTUAL")

    def test_context_copy_with_preserves_immutability(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(), "corr-imm"
        )
        ctx2 = ctx.copy_with(active_state="IN_TRANSIT", confidence_score=0.75)
        self.assertEqual(ctx.active_state, "PRE_DEPARTURE")
        self.assertEqual(ctx2.active_state, "IN_TRANSIT")
        self.assertEqual(ctx2.confidence_score, 0.75)
        self.assertEqual(ctx2.correlation_id, "corr-imm")


class TestAlertEngine(unittest.TestCase):
    """Alert deduplication and severity mapping."""

    def setUp(self):
        self.engine = AlertEngine()

    def test_low_drift_suppresses_alert(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=5.0), "c-1"
        )
        self.assertEqual(len(self.engine.evaluate_alerts(ctx)), 0)

    def test_high_drift_fires_alert(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=25.0), "c-2"
        )
        alerts = self.engine.evaluate_alerts(ctx)
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].priority, "HIGH")

    def test_platform_change_fires_critical_alert(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(platform_changed=True), "c-3"
        )
        alerts = self.engine.evaluate_alerts(ctx)
        self.assertTrue(any(a.priority == "CRITICAL" for a in alerts))

    def test_exact_threshold_no_alert(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=10.0), "c-4"
        )
        self.assertEqual(len(self.engine.evaluate_alerts(ctx)), 0)


class TestActionEngine(unittest.TestCase):
    """Catalog-driven action selector checks."""

    def setUp(self):
        self.engine = ActionEngine()

    def test_platform_changed_action(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(platform_changed=True), "c-act1"
        )
        action = self.engine.select_action(ctx)
        self.assertEqual(action["action_code"], "CHANGE_PLATFORM")
        self.assertEqual(action["urgency"], "CRITICAL")

    def test_high_drift_action(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=45.0), "c-act2"
        )
        action = self.engine.select_action(ctx)
        self.assertEqual(action["action_code"], "LEAVE_EARLIER")

    def test_nominal_action(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-act3")
        action = self.engine.select_action(ctx)
        self.assertEqual(action["action_code"], "WAIT")


class TestTimelineEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TimelineEngine()

    def test_no_drift_returns_v1(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=0.0), "c-tl1"
        )
        tl = self.engine.evaluate_timeline(ctx)
        self.assertEqual(tl.version, "T_V1")
        self.assertEqual(len(tl.events), 2)

    def test_drift_returns_v2(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=12.0), "c-tl2"
        )
        tl = self.engine.evaluate_timeline(ctx)
        self.assertEqual(tl.version, "T_V2")
        self.assertAlmostEqual(tl.events[1].variance_minutes, 12.0)


class TestRiskEngine(unittest.TestCase):
    def setUp(self):
        self.engine = RiskEngine()

    def test_low_drift_safe(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=5.0), "c-r1"
        )
        self.assertEqual(self.engine.calculate_risk(ctx)["risk_level"], "LOW")

    def test_high_drift_risky(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=25.0), "c-r2"
        )
        self.assertEqual(self.engine.calculate_risk(ctx)["risk_level"], "HIGH")


class TestConfidenceEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ConfidenceEngine()

    def test_nominal_confidence(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-cf1")
        self.assertEqual(self.engine.calculate_confidence(ctx), 0.98)

    def test_degraded_confidence(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=40.0), "c-cf2"
        )
        self.assertEqual(self.engine.calculate_confidence(ctx), 0.85)


class TestExplanationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = ExplanationEngine()

    def test_punctual_explanation(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-ex1")
        exp = self.engine.generate_explanation(ctx)
        self.assertEqual(exp["reason_code"], "E_PUNCTUAL")

    def test_platform_swap_explanation(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(platform_changed=True), "c-ex2"
        )
        exp = self.engine.generate_explanation(ctx)
        self.assertEqual(exp["reason_code"], "EXP_PLATFORM_SWAP")

    def test_delay_explanation(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(drift_minutes=45.0), "c-ex3"
        )
        exp = self.engine.generate_explanation(ctx)
        self.assertEqual(exp["reason_code"], "EXP_TRAIN_DELAYED")


class TestPrioritySuppressionEscalation(unittest.TestCase):
    def test_priority_engine(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-pr1")
        self.assertEqual(PriorityEngine().resolve_priority(ctx), "HIGH")

    def test_suppression_off_by_default(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-su1")
        self.assertFalse(SuppressionEngine().apply_suppression(ctx))

    def test_suppression_during_sleep(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(is_sleeping_hours=True), "c-su2"
        )
        self.assertTrue(SuppressionEngine().apply_suppression(ctx))

    def test_escalation_off_by_default(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-esc1")
        self.assertFalse(EscalationEngine().check_escalation(ctx))


class TestEventEngine(unittest.TestCase):
    def setUp(self):
        self.engine = EventEngine()

    def test_parse_platform_change(self):
        raw = {
            "event_id": "e1",
            "event_type": "PLATFORM_CHANGE",
            "timestamp": 123456.0,
        }
        dto = self.engine.parse_raw_event(raw)
        self.assertEqual(dto.event_type, "PLATFORM_CHANGE")
        self.assertEqual(dto.severity, "CRITICAL")

    def test_parse_unknown_defaults_low(self):
        dto = self.engine.parse_raw_event({})
        self.assertEqual(dto.severity, "LOW")


class TestPolicyResolver(unittest.TestCase):
    def test_known_policy(self):
        pr = PolicyResolver()
        policy = pr.resolve_policy("Alert")
        self.assertIn("deduplication_delta_minutes", policy)

    def test_unknown_policy_returns_empty(self):
        self.assertEqual(PolicyResolver().resolve_policy("NonExistent"), {})


class TestCacheManager(unittest.TestCase):
    def test_local_cache_roundtrip(self):
        cm = TravelerCacheManager()
        _run(cm.set_cached("k1", {"a": 1}, 60))
        result = _run(cm.get_cached("k1"))
        self.assertEqual(result, {"a": 1})

    def test_local_cache_miss(self):
        cm = TravelerCacheManager()
        self.assertIsNone(_run(cm.get_cached("nonexistent")))


class TestHealthEngine(unittest.TestCase):
    def test_health_up(self):
        h = HealthEngine()
        status = h.check_health()
        self.assertEqual(status["status"], "UP")


class TestConfigRegistry(unittest.TestCase):
    def test_feature_flag_known(self):
        self.assertTrue(is_feature_enabled("ENABLE_RECOVERY_ENGINE"))

    def test_feature_flag_unknown(self):
        self.assertFalse(is_feature_enabled("DOES_NOT_EXIST"))

    def test_get_policy(self):
        p = get_policy("Priority")
        self.assertIn("EMERGENCY", p)

    def test_get_policy_unknown(self):
        self.assertEqual(get_policy("Unknown"), {})


class TestRecoveryEngine(unittest.TestCase):
    def test_recovery_plan_returned(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-rec")
        recovery = _run(RecoveryEngine().build_recovery_plan(None, ctx))
        self.assertEqual(recovery.incident_type, "CONNECTION_MISSED")
        self.assertTrue(len(recovery.alternative_options) > 0)


class TestReminderEngine(unittest.TestCase):
    def test_departure_reminder_generated(self):
        future_dep = 9999999999.0
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(scheduled_departure=future_dep), "c-rem"
        )
        reminders = ReminderEngine().process_reminders(ctx)
        self.assertTrue(len(reminders) >= 1)
        self.assertEqual(reminders[0].reminder_id, "rem_leave_home")


class TestCheckpointEngine(unittest.TestCase):
    def test_verify_returns_list(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-chk")
        self.assertIsInstance(CheckpointEngine().verify_checkpoints(ctx), list)


class TestGuidanceEngine(unittest.TestCase):
    def test_compile_returns_dto(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-guid")
        g = GuidanceEngine().compile_guidance(ctx)
        self.assertEqual(g.traveler_id, "usr_99")


# ===================================================================
# 2. STRATEGY & SCENARIO REGISTRY TESTS
# ===================================================================


class TestTravelerStrategyRegistry(unittest.TestCase):
    def test_default_registry_has_all_strategies(self):
        reg = TravelerStrategyRegistry.create_default()
        expected = [
            "SAFETY_FIRST",
            "BUSINESS_TRAVELER",
            "FAMILY_TRAVELER",
            "MEDICAL_TRAVELER",
            "TOURIST",
            "MINIMAL_WALKING",
            "FAST_RECOVERY",
            "BUDGET_PROTECTION",
            "ACCESSIBILITY",
            "LOW_STRESS",
        ]
        for key in expected:
            self.assertIsNotNone(reg.get(key), f"Missing strategy: {key}")

    def test_safety_first_strategy(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-sf")
        result = SafetyFirstStrategy().evaluate(ctx)
        self.assertEqual(result["action_code"], "LEAVE_EARLIER")

    def test_medical_strategy(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-med")
        result = MedicalTravelerStrategy().evaluate(ctx)
        self.assertEqual(result["action_code"], "STEP_FREE_PATH")

    def test_unknown_strategy_returns_none(self):
        reg = TravelerStrategyRegistry.create_default()
        self.assertIsNone(reg.get("NONEXISTENT"))


class TestScenarioRegistry(unittest.TestCase):
    def test_platform_changed_scenario_matches(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(platform_changed=True), "c-sc1"
        )
        s = PlatformChangedScenario()
        self.assertTrue(s.matches(ctx))
        self.assertEqual(s.evaluate(ctx)["scenario"], "PLATFORM_CHANGED")

    def test_train_cancelled_scenario_matches(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(cancelled=True), "c-sc2"
        )
        self.assertTrue(TrainCancelledScenario().matches(ctx))

    def test_medical_emergency_scenario(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(medical_emergency=True), "c-sc3"
        )
        result = MedicalEmergencyScenario().evaluate(ctx)
        self.assertEqual(result["urgency"], "EMERGENCY")

    def test_wheelchair_scenario(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(wheelchair_required=True), "c-sc4"
        )
        result = WheelchairTravelerScenario().evaluate(ctx)
        self.assertEqual(result["action_code"], "STEP_FREE_PATH")

    def test_default_registry_evaluate_all(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(platform_changed=True, drift_minutes=20.0), "c-sc5"
        )
        reg = ScenarioRegistry.create_default()
        results = reg.evaluate_all(ctx)
        scenarios = [r["scenario"] for r in results]
        self.assertIn("PLATFORM_CHANGED", scenarios)
        self.assertIn("LATE_ARRIVAL", scenarios)

    def test_no_match_returns_empty(self):
        ctx = TravelerDecisionContextFactory.create_context(_make_telemetry(), "c-sc6")
        reg = ScenarioRegistry.create_default()
        self.assertEqual(reg.evaluate_all(ctx), [])

    def test_first_match_returns_single(self):
        ctx = TravelerDecisionContextFactory.create_context(
            _make_telemetry(cancelled=True), "c-sc7"
        )
        reg = ScenarioRegistry.create_default()
        result = reg.first_match(ctx)
        self.assertIsNotNone(result)
        self.assertEqual(result["scenario"], "TRAIN_CANCELLED")


# ===================================================================
# 3. ERROR TAXONOMY TESTS
# ===================================================================


class TestErrorTaxonomy(unittest.TestCase):
    def test_all_errors_inherit_traveler_error(self):
        for cls in [
            ContextError,
            TimelineError,
            CheckpointError,
            AlertError,
            RecoveryError,
            ExplanationError,
            PolicyError,
        ]:
            with self.subTest(cls=cls.__name__):
                err = cls()
                self.assertIsInstance(err, TravelerError)

    def test_error_codes(self):
        self.assertEqual(ContextError().code, "ERR_T_CTX")
        self.assertEqual(TimelineError().code, "ERR_T_TIM")
        self.assertEqual(CheckpointError().code, "ERR_T_CKP")
        self.assertEqual(AlertError().code, "ERR_T_ALT")
        self.assertEqual(RecoveryError().code, "ERR_T_REC")
        self.assertEqual(ExplanationError().code, "ERR_T_EXP")
        self.assertEqual(PolicyError().code, "ERR_T_POL")

    def test_custom_message(self):
        err = ContextError("bad payload")
        self.assertIn("bad payload", str(err))


# ===================================================================
# 4. INTEGRATION TESTS
# ===================================================================


class TestFullPipelineIntegration(unittest.TestCase):
    """End-to-end gateway → coordinator → pipeline → guidance tests."""

    def setUp(self):
        self.gateway = _build_gateway()

    def test_nominal_journey(self):
        guidance = _run(
            self.gateway.process_telemetry_update(_make_telemetry(), "corr-nominal")
        )
        self.assertEqual(guidance.correlation_id, "corr-nominal")
        self.assertEqual(guidance.status, "PUNCTUAL")
        self.assertEqual(guidance.recommended_action.action_code, "WAIT")
        self.assertEqual(guidance.confidence_score, 0.98)

    def test_platform_swap_pipeline(self):
        guidance = _run(
            self.gateway.process_telemetry_update(
                _make_telemetry(drift_minutes=45.0, platform_changed=True),
                "corr-swap",
            )
        )
        self.assertEqual(guidance.recommended_action.action_code, "CHANGE_PLATFORM")
        self.assertEqual(guidance.explanation.reason_code, "EXP_PLATFORM_SWAP")
        self.assertEqual(guidance.confidence_score, 0.85)

    def test_heavy_delay_pipeline(self):
        guidance = _run(
            self.gateway.process_telemetry_update(
                _make_telemetry(drift_minutes=60.0), "corr-delay"
            )
        )
        self.assertEqual(guidance.recommended_action.action_code, "LEAVE_EARLIER")
        self.assertEqual(guidance.explanation.reason_code, "EXP_TRAIN_DELAYED")

    def test_latency_budget(self):
        """Pipeline must complete within 100ms hard cap."""
        import time

        start = time.time()
        _run(
            self.gateway.process_telemetry_update(
                _make_telemetry(drift_minutes=15.0), "corr-perf"
            )
        )
        elapsed_ms = (time.time() - start) * 1000
        self.assertLess(elapsed_ms, 100.0, "Pipeline exceeded 100ms hard cap")


# ===================================================================
# 5. BOUNDARY TESTS  (Planning §31 – No GDS Leaks)
# ===================================================================


class TestBoundaryImportConstraints(unittest.TestCase):
    """Verify no GDS / integration adapters are imported in app/traveler/."""

    FORBIDDEN_PREFIXES = (
        "app.integration",
        "app.gds",
        "firebase_admin",
        "twilio",
        "sendgrid",
        "boto3",
    )

    def test_no_gds_imports_in_traveler_package(self):
        traveler_root = os.path.join(os.path.dirname(__file__), os.pardir, "traveler")
        traveler_root = os.path.abspath(traveler_root)

        violations = []
        for dirpath, _dirnames, filenames in os.walk(traveler_root):
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                filepath = os.path.join(dirpath, fname)
                with open(filepath, encoding="utf-8") as fh:
                    try:
                        tree = ast.parse(fh.read(), filename=filepath)
                    except SyntaxError:
                        continue
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name.startswith(self.FORBIDDEN_PREFIXES):
                                violations.append(f"{filepath}: import {alias.name}")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and node.module.startswith(
                            self.FORBIDDEN_PREFIXES
                        ):
                            violations.append(
                                f"{filepath}: from {node.module} import ..."
                            )

        self.assertEqual(
            violations,
            [],
            "GDS/provider import leaks detected:\n" + "\n".join(violations),
        )


if __name__ == "__main__":
    unittest.main()
