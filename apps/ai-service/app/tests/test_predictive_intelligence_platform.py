"""
Comprehensive Test Suite for Phase 7 Predictive Intelligence Platform.
Validates all 9 Functional Requirements (FR-1 through FR-9), 8 Capabilities (CP-1 through CP-8),
DPDP consent checks, explainability, learning loops, and REST API router integration.
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.predictive_router import router as predictive_router
from app.predictive.interfaces import (
    JourneyContext,
    PassengerProfileContext,
    RiskLevel,
    ConsentStatus,
    ConfidenceLevel,
    LearningOutcomeSignal,
)
from app.predictive.waitlist import WaitlistForecaster
from app.predictive.delay import ArrivalDelayPredictor
from app.predictive.seat import DynamicSeatProjectionEngine
from app.predictive.congestion import StationCongestionForecaster
from app.predictive.risk import MultiSegmentRiskMonitor
from app.predictive.recommendation import AlternativeTravelOrchestrator
from app.predictive.notification import ProactiveAlertDispatcher
from app.predictive.personalization import PersonalizedDecisionSupportEngine
from app.predictive.explainability import NaturalLanguageGuidanceEngine
from app.predictive.governance import PredictiveGovernanceController
from app.predictive.learning import ContinuousLearningCoordinator
from app.predictive.orchestrator import PredictiveIntelligenceOrchestrator


@pytest.fixture
def journey_sample():
    return JourneyContext(
        train_number="12301",
        origin_station="HWH",
        destination_station="NDLS",
        travel_date="2026-08-15",
        booking_class="3A",
        quota="GN",
        waitlist_position=12,
        connecting_train_number="12951",
        transfer_station="NDLS",
        transfer_buffer_mins=45,
        weather_condition="fog",
    )


@pytest.fixture
def passenger_sample():
    return PassengerProfileContext(
        traveler_id="TRV-998822",
        risk_tolerance=RiskLevel.MEDIUM,
        preferred_class="3A",
        consent_status=ConsentStatus.GRANTED,
        historical_trip_count=14,
    )


# --- FR-1: Waitlist Confirmation Probability ---
def test_waitlist_forecaster(journey_sample):
    forecaster = WaitlistForecaster()
    result = asyncio.run(forecaster.predict_confirmation(journey_sample))

    assert result.train_number == "12301"
    assert result.waitlist_position == 12
    assert 0.0 <= result.confirmation_probability <= 100.0
    assert result.confidence_score > 0.0
    assert result.confidence_level in (ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW)

    # Test confirmed status (position = 0)
    confirmed_journey = journey_sample.model_copy(update={"waitlist_position": 0})
    confirmed_res = asyncio.run(forecaster.predict_confirmation(confirmed_journey))
    assert confirmed_res.confirmation_probability == 100.0
    assert confirmed_res.confidence_level == ConfidenceLevel.HIGH


# --- FR-2: Arrival Delay Projections ---
def test_arrival_delay_predictor(journey_sample):
    predictor = ArrivalDelayPredictor()

    # Clear weather
    clear_journey = journey_sample.model_copy(update={"weather_condition": "clear"})
    clear_res = asyncio.run(predictor.predict_delay(clear_journey))
    assert clear_res.predicted_delay_mins > 0

    # Fog weather (should increase delay)
    fog_res = asyncio.run(predictor.predict_delay(journey_sample))
    assert fog_res.predicted_delay_mins > clear_res.predicted_delay_mins
    assert fog_res.weather_impact_mins > 0


# --- FR-3: Dynamic Seat Availability Projections ---
def test_dynamic_seat_projection(journey_sample):
    engine = DynamicSeatProjectionEngine()
    result = asyncio.run(engine.project_seat_availability(journey_sample))

    assert result.available_seats > 0
    assert result.projected_exhaustion_hours > 0.0
    assert 0.0 <= result.quota_conversion_rate <= 100.0


# --- FR-4: Station & Platform Congestion Forecasting ---
def test_station_congestion_forecaster():
    forecaster = StationCongestionForecaster()

    # Peak hour at junction NDLS
    ndls_res = asyncio.run(forecaster.forecast_congestion("NDLS", arrival_hour=8))
    assert ndls_res.crowd_density_level in (RiskLevel.HIGH, RiskLevel.MEDIUM)
    assert ndls_res.queue_length_est > 10

    # Non-peak hour at local station
    local_res = asyncio.run(forecaster.forecast_congestion("STN", arrival_hour=14))
    assert local_res.crowd_density_level == RiskLevel.LOW


# --- FR-6: Multi-Segment Journey Risk Monitor ---
def test_multi_segment_risk_monitor(journey_sample):
    predictor = ArrivalDelayPredictor()
    monitor = MultiSegmentRiskMonitor()

    async def _run():
        delay = await predictor.predict_delay(journey_sample)
        risk = await monitor.evaluate_connection_risk(journey_sample, delay)
        return risk

    risk = asyncio.run(_run())
    assert risk.journey_id.startswith("J-12301")
    assert 0.0 <= risk.missed_connection_probability <= 100.0
    assert risk.risk_level in (RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL)

    # Test single-segment (no connection)
    single_journey = journey_sample.model_copy(update={"connecting_train_number": None})
    async def _run_single():
        delay = await predictor.predict_delay(single_journey)
        return await monitor.evaluate_connection_risk(single_journey, delay)

    single_risk = asyncio.run(_run_single())
    assert single_risk.missed_connection_probability == 0.0
    assert single_risk.risk_level == RiskLevel.LOW


# --- FR-5: Alternative Travel Orchestration ---
def test_alternative_travel_orchestrator(journey_sample, passenger_sample):
    predictor = ArrivalDelayPredictor()
    monitor = MultiSegmentRiskMonitor()
    orchestrator = AlternativeTravelOrchestrator()

    async def _run():
        delay = await predictor.predict_delay(journey_sample)
        risk = await monitor.evaluate_connection_risk(journey_sample, delay)
        return await orchestrator.generate_alternatives(journey_sample, risk, passenger_sample)

    recs = asyncio.run(_run())
    assert recs.original_train == "12301"
    assert len(recs.recommended_alternatives) > 0
    assert recs.recommended_alternatives[0].match_score > 0.0


# --- FR-7: Proactive Event Alerts ---
def test_proactive_alert_dispatcher(journey_sample, passenger_sample):
    predictor = ArrivalDelayPredictor()
    monitor = MultiSegmentRiskMonitor()
    dispatcher = ProactiveAlertDispatcher()

    # Trigger high risk
    high_risk_journey = journey_sample.model_copy(update={"transfer_buffer_mins": 5})
    async def _run():
        delay = await predictor.predict_delay(high_risk_journey)
        risk = await monitor.evaluate_connection_risk(high_risk_journey, delay)
        return await dispatcher.evaluate_and_dispatch_alert(risk, delay, passenger_sample)

    alert = asyncio.run(_run())
    assert alert is not None
    assert alert.alert_type == "CONNECTION_RISK_WARNING"
    assert alert.actionable_recommendation is not None


# --- FR-8: Personalized Decision Support ---
def test_personalized_decision_support(journey_sample, passenger_sample):
    predictor = ArrivalDelayPredictor()
    monitor = MultiSegmentRiskMonitor()
    orchestrator = AlternativeTravelOrchestrator()
    personalizer = PersonalizedDecisionSupportEngine()

    async def _run():
        delay = await predictor.predict_delay(journey_sample)
        risk = await monitor.evaluate_connection_risk(journey_sample, delay)
        recs = await orchestrator.generate_alternatives(journey_sample, risk, passenger_sample)
        return await personalizer.personalize_decision_support(passenger_sample, risk, recs)

    personalized_recs = asyncio.run(_run())
    assert len(personalized_recs.recommended_alternatives) > 0


# --- FR-9: Natural Language Guidance & Explainability ---
def test_natural_language_guidance(journey_sample):
    guidance = NaturalLanguageGuidanceEngine()
    forecaster = WaitlistForecaster()

    wl_pred = asyncio.run(forecaster.predict_confirmation(journey_sample))
    wrapped = guidance.wrap_waitlist_prediction(wl_pred)

    assert wrapped.prediction_id.startswith("PRED-WL-")
    assert wrapped.confidence_score > 0.0
    assert len(wrapped.explanation_text) > 20
    assert len(wrapped.evidence_trail) >= 2


# --- CP-7: Governance & DPDP Consent ---
def test_predictive_governance(passenger_sample):
    controller = PredictiveGovernanceController()

    # Valid consent
    assert controller.validate_consent(passenger_sample) is True

    # Denied consent
    denied_passenger = passenger_sample.model_copy(update={"consent_status": ConsentStatus.DENIED})
    assert controller.validate_consent(denied_passenger) is False


# --- CP-8: Continuous Learning Coordinator ---
def test_continuous_learning_coordinator():
    coordinator = ContinuousLearningCoordinator()
    signal = LearningOutcomeSignal(
        prediction_id="PRED-DEL-1001",
        train_number="12301",
        actual_delay_mins=25,
        error_margin=3.0,
        timestamp="2026-08-15T12:00:00Z",
    )

    res = coordinator.register_physical_outcome(signal)
    assert res["registered"] is True
    assert res["current_mae"] == 3.0

    metrics = coordinator.get_accuracy_metrics()
    assert metrics["logged_outcomes_count"] == 1
    assert metrics["model_health_status"] == "OPTIMAL"


# --- Orchestrator End-to-End Test ---
def test_predictive_orchestrator_full_package(journey_sample, passenger_sample):
    orchestrator = PredictiveIntelligenceOrchestrator()

    pkg = asyncio.run(orchestrator.execute_full_journey_foresight_package(journey_sample, passenger_sample))

    assert "waitlist_foresight" in pkg
    assert "delay_foresight" in pkg
    assert "connection_risk_foresight" in pkg
    assert "station_congestion_forecast" in pkg
    assert "alternative_recommendations" in pkg
    assert pkg["governance_status"]["dpdp_consent_verified"] is True

    # Test consent denied flow
    denied_passenger = passenger_sample.model_copy(update={"consent_status": ConsentStatus.DENIED})
    denied_pkg = asyncio.run(orchestrator.execute_full_journey_foresight_package(journey_sample, denied_passenger))
    assert "error" in denied_pkg
    assert denied_pkg["error"] == "DPDP Consent Denied"


# --- REST API Endpoints Integration Test ---
def test_predictive_api_endpoints(journey_sample, passenger_sample):
    app.include_router(predictive_router)
    test_client = TestClient(app)
    payload = {
        "journey": journey_sample.model_dump(),
        "passenger": passenger_sample.model_dump(),
    }

    # 1. Waitlist endpoint
    res_wl = test_client.post("/api/predictive/waitlist", json=payload)
    assert res_wl.status_code == 200
    data_wl = res_wl.json()
    assert data_wl["prediction_type"] == "WAITLIST_PROBABILITY"

    # 2. Delay endpoint
    res_del = test_client.post("/api/predictive/delay", json=payload)
    assert res_del.status_code == 200
    data_del = res_del.json()
    assert data_del["prediction_type"] == "ARRIVAL_DELAY"

    # 3. Risk endpoint
    res_rsk = test_client.post("/api/predictive/risk", json=payload)
    assert res_rsk.status_code == 200
    data_rsk = res_rsk.json()
    assert data_rsk["prediction_type"] == "MULTI_SEGMENT_RISK"

    # 4. Alternatives endpoint
    res_alt = test_client.post("/api/predictive/alternatives", json=payload)
    assert res_alt.status_code == 200
    data_alt = res_alt.json()
    assert "recommended_alternatives" in data_alt

    # 5. Congestion endpoint
    res_cng = test_client.get("/api/predictive/congestion/NDLS?arrival_hour=9")
    assert res_cng.status_code == 200
    data_cng = res_cng.json()
    assert data_cng["station_code"] == "NDLS"

    # 6. Full Foresight Package endpoint
    res_pkg = test_client.post("/api/predictive/foresight", json=payload)
    assert res_pkg.status_code == 200
    data_pkg = res_pkg.json()
    assert "waitlist_foresight" in data_pkg

    # 7. Health endpoint
    res_hlth = test_client.get("/api/predictive/health")
    assert res_hlth.status_code == 200
    data_hlth = res_hlth.json()
    assert data_hlth["status"] == "HEALTHY"
