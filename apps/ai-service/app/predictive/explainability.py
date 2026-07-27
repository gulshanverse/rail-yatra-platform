"""
Natural Language Guidance & Explainability Engine (FR-9, Trust Domain).
"""

import uuid
import logging
from typing import Any
from app.predictive.interfaces import (
    PredictionType,
    CalibratedPredictionOutput,
    ConfidenceLevel,
    WaitlistPrediction,
    DelayPrediction,
    RiskEvaluation,
)

logger = logging.getLogger("ai-service.predictive.explainability")


class NaturalLanguageGuidanceEngine:
    """
    Explainability Engine for wrapping predictions in plain-language guidance and evidence (FR-9).
    """

    def wrap_waitlist_prediction(self, pred: WaitlistPrediction) -> CalibratedPredictionOutput:
        explanation = (
            f"Your waitlist position {pred.waitlist_position} in {pred.booking_class} on Train {pred.train_number} "
            f"has an estimated {pred.confirmation_probability}% confirmation probability ({pred.confidence_level.value} confidence). "
            f"Expected clearance trend is {pred.clearing_trend.replace('_', ' ').title()} over approx {pred.estimated_clearance_days} days."
        )

        evidence = [
            f"Historical clearance density: {pred.historical_data_density} past bookings evaluated",
            f"Booking class baseline clearance rate: {pred.booking_class}",
            f"Calculated statistical confidence score: {pred.confidence_score}",
        ]

        return CalibratedPredictionOutput(
            prediction_id=f"PRED-WL-{uuid.uuid4().hex[:8].upper()}",
            prediction_type=PredictionType.WAITLIST_PROBABILITY,
            primary_value=pred.confirmation_probability,
            confidence_score=pred.confidence_score,
            confidence_level=pred.confidence_level,
            explanation_text=explanation,
            evidence_trail=evidence,
            consent_verified=True,
            metadata=pred.model_dump(),
        )

    def wrap_delay_prediction(self, pred: DelayPrediction) -> CalibratedPredictionOutput:
        explanation = (
            f"Train {pred.train_number} arriving at {pred.station_code} is projected to be delayed by {pred.predicted_delay_mins} minutes "
            f"({pred.delay_severity} severity, {pred.confidence_level.value} confidence). "
            f"Weather factors contribute approximately {pred.weather_impact_mins} minutes of this delay horizon."
        )

        evidence = [
            f"Historical route on-time performance: {pred.historical_on_time_percent}%",
            f"Weather impact add-on: {pred.weather_impact_mins} mins",
            f"Confidence score: {pred.confidence_score}",
        ]

        return CalibratedPredictionOutput(
            prediction_id=f"PRED-DEL-{uuid.uuid4().hex[:8].upper()}",
            prediction_type=PredictionType.ARRIVAL_DELAY,
            primary_value=pred.predicted_delay_mins,
            confidence_score=pred.confidence_score,
            confidence_level=pred.confidence_level,
            explanation_text=explanation,
            evidence_trail=evidence,
            consent_verified=True,
            metadata=pred.model_dump(),
        )

    def wrap_risk_evaluation(self, risk: RiskEvaluation) -> CalibratedPredictionOutput:
        explanation = (
            f"Connection risk for transfer at {risk.connecting_train_number or 'station'} is assessed as {risk.risk_level.value} "
            f"with a {risk.missed_connection_probability}% chance of missed connection. "
            f"Estimated remaining safety buffer is {risk.safety_margin_mins} minutes."
        )

        evidence = [
            f"Transfer safety margin: {risk.safety_margin_mins} mins",
            f"Vulnerability factors identified: {', '.join(risk.vulnerability_factors)}",
        ]

        confidence_level = ConfidenceLevel.HIGH if risk.safety_margin_mins > 30 else ConfidenceLevel.MEDIUM

        return CalibratedPredictionOutput(
            prediction_id=f"PRED-RSK-{uuid.uuid4().hex[:8].upper()}",
            prediction_type=PredictionType.MULTI_SEGMENT_RISK,
            primary_value=risk.missed_connection_probability,
            confidence_score=0.90 if confidence_level == ConfidenceLevel.HIGH else 0.78,
            confidence_level=confidence_level,
            explanation_text=explanation,
            evidence_trail=evidence,
            consent_verified=True,
            metadata=risk.model_dump(),
        )
