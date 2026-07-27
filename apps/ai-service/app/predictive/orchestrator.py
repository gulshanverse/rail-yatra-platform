"""
Predictive Intelligence Platform Orchestrator.
Main entry point orchestrating all predictive capabilities (FR-1 through FR-9, CP-1 through CP-8).
"""

import logging
from typing import Dict, Any, Optional
from app.predictive.interfaces import (
    PassengerProfileContext,
    JourneyContext,
    SeatAvailabilityProjection,
    StationCongestionForecast,
    AlternativeJourneyRecommendation,
    CalibratedPredictionOutput,
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

logger = logging.getLogger("ai-service.predictive.orchestrator")


class PredictiveIntelligenceOrchestrator:
    """
    Central orchestrator managing all Predictive Intelligence capabilities.
    """

    def __init__(self):
        self.waitlist_forecaster = WaitlistForecaster()
        self.delay_predictor = ArrivalDelayPredictor()
        self.seat_engine = DynamicSeatProjectionEngine()
        self.congestion_forecaster = StationCongestionForecaster()
        self.risk_monitor = MultiSegmentRiskMonitor()
        self.alternative_orchestrator = AlternativeTravelOrchestrator()
        self.alert_dispatcher = ProactiveAlertDispatcher()
        self.personalization_engine = PersonalizedDecisionSupportEngine()
        self.guidance_engine = NaturalLanguageGuidanceEngine()
        self.governance_controller = PredictiveGovernanceController()
        self.learning_coordinator = ContinuousLearningCoordinator()

    async def get_waitlist_confirmation_foresight(
        self, journey: JourneyContext, passenger: Optional[PassengerProfileContext] = None
    ) -> CalibratedPredictionOutput:
        passenger_ctx = passenger or PassengerProfileContext(traveler_id="ANONYMOUS")
        if not self.governance_controller.validate_consent(passenger_ctx):
            raise PermissionError("DPDP Consent denied for personalized waitlist prediction.")

        self.governance_controller.sanitize_profile_for_prediction(passenger_ctx)
        pred = await self.waitlist_forecaster.predict_confirmation(journey)
        wrapped = self.guidance_engine.wrap_waitlist_prediction(pred)
        return self.governance_controller.audit_prediction_payload(wrapped)

    async def get_delay_foresight(
        self, journey: JourneyContext, passenger: Optional[PassengerProfileContext] = None
    ) -> CalibratedPredictionOutput:
        passenger_ctx = passenger or PassengerProfileContext(traveler_id="ANONYMOUS")
        if not self.governance_controller.validate_consent(passenger_ctx):
            raise PermissionError("DPDP Consent denied for delay prediction.")

        pred = await self.delay_predictor.predict_delay(journey)
        wrapped = self.guidance_engine.wrap_delay_prediction(pred)
        return self.governance_controller.audit_prediction_payload(wrapped)

    async def get_seat_availability_foresight(self, journey: JourneyContext) -> SeatAvailabilityProjection:
        return await self.seat_engine.project_seat_availability(journey)

    async def get_station_congestion_foresight(self, station_code: str, arrival_hour: int = 14) -> StationCongestionForecast:
        return await self.congestion_forecaster.forecast_congestion(station_code, arrival_hour)

    async def get_connection_risk_foresight(
        self, journey: JourneyContext, passenger: Optional[PassengerProfileContext] = None
    ) -> CalibratedPredictionOutput:
        passenger_ctx = passenger or PassengerProfileContext(traveler_id="ANONYMOUS")
        if not self.governance_controller.validate_consent(passenger_ctx):
            raise PermissionError("DPDP Consent denied for risk prediction.")

        delay_pred = await self.delay_predictor.predict_delay(journey)
        risk_eval = await self.risk_monitor.evaluate_connection_risk(journey, delay_pred)
        wrapped = self.guidance_engine.wrap_risk_evaluation(risk_eval)
        return self.governance_controller.audit_prediction_payload(wrapped)

    async def get_alternative_orchestration(
        self, journey: JourneyContext, passenger: Optional[PassengerProfileContext] = None
    ) -> AlternativeJourneyRecommendation:
        passenger_ctx = passenger or PassengerProfileContext(traveler_id="ANONYMOUS")
        delay_pred = await self.delay_predictor.predict_delay(journey)
        risk_eval = await self.risk_monitor.evaluate_connection_risk(journey, delay_pred)

        recommendation = await self.alternative_orchestrator.generate_alternatives(journey, risk_eval, passenger_ctx)
        return await self.personalization_engine.personalize_decision_support(passenger_ctx, risk_eval, recommendation)

    async def execute_full_journey_foresight_package(
        self, journey: JourneyContext, passenger: Optional[PassengerProfileContext] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end journey protection foresight (FR-1 through FR-9).
        """
        passenger_ctx = passenger or PassengerProfileContext(traveler_id="ANONYMOUS")

        # 1. Audit Consent
        if not self.governance_controller.validate_consent(passenger_ctx):
            return {
                "error": "DPDP Consent Denied",
                "message": "Passenger has not granted consent for predictive travel insights.",
            }

        # 2. Ingest Predictions
        wl_output = await self.get_waitlist_confirmation_foresight(journey, passenger_ctx)
        delay_output = await self.get_delay_foresight(journey, passenger_ctx)
        risk_output = await self.get_connection_risk_foresight(journey, passenger_ctx)
        seat_proj = await self.get_seat_availability_foresight(journey)
        congestion_proj = await self.get_station_congestion_foresight(journey.destination_station)

        # 3. Alternatives & Personalization
        delay_pred = await self.delay_predictor.predict_delay(journey)
        risk_eval = await self.risk_monitor.evaluate_connection_risk(journey, delay_pred)
        alternatives = await self.alternative_orchestrator.generate_alternatives(journey, risk_eval, passenger_ctx)
        personalized_alts = await self.personalization_engine.personalize_decision_support(passenger_ctx, risk_eval, alternatives)

        # 4. Proactive Alerting
        proactive_alert = await self.alert_dispatcher.evaluate_and_dispatch_alert(risk_eval, delay_pred, passenger_ctx)

        logger.info(
            f"Executed Full Journey Foresight Package for Train {journey.train_number} (Traveler: {passenger_ctx.traveler_id})"
        )

        return {
            "journey_info": journey.model_dump(),
            "passenger_context": passenger_ctx.model_dump(),
            "waitlist_foresight": wl_output.model_dump(),
            "delay_foresight": delay_output.model_dump(),
            "connection_risk_foresight": risk_output.model_dump(),
            "seat_availability_projection": seat_proj.model_dump(),
            "station_congestion_forecast": congestion_proj.model_dump(),
            "alternative_recommendations": personalized_alts.model_dump(),
            "proactive_alert": proactive_alert.model_dump() if proactive_alert else None,
            "governance_status": {
                "dpdp_consent_verified": True,
                "pii_redacted": True,
                "ethics_calibrated": True,
            },
        }

    def register_outcome_signal(self, signal: LearningOutcomeSignal) -> Dict[str, Any]:
        return self.learning_coordinator.register_physical_outcome(signal)

    def get_learning_metrics(self) -> Dict[str, Any]:
        return self.learning_coordinator.get_accuracy_metrics()


# Global singleton instance
predictive_orchestrator = PredictiveIntelligenceOrchestrator()
