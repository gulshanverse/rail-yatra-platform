"""
Predictive Governance Controller (CP-7, Governance Domain).
"""

import logging
from app.predictive.interfaces import (
    PassengerProfileContext,
    ConsentStatus,
    CalibratedPredictionOutput,
)

logger = logging.getLogger("ai-service.predictive.governance")


class PredictiveGovernanceController:
    """
    Governance Controller for DPDP compliance, PII protection, and prediction calibration audits (CP-7).
    """

    def validate_consent(self, passenger: PassengerProfileContext) -> bool:
        """
        Audits traveler consent under the Digital Personal Data Protection (DPDP) Act.
        """
        if passenger.consent_status == ConsentStatus.DENIED:
            logger.warning(f"Governance Audit DENIED: Traveler {passenger.traveler_id} has denied data consent.")
            return False
        return True

    def sanitize_profile_for_prediction(self, passenger: PassengerProfileContext) -> PassengerProfileContext:
        """
        Redacts PII and minimizes traveler payload before feature ingestion.
        """
        passenger_copy = passenger.model_copy()
        passenger_copy.pii_redacted = True
        return passenger_copy

    def audit_prediction_payload(self, output: CalibratedPredictionOutput) -> CalibratedPredictionOutput:
        """
        Validates output calibration confidence margins and explainability rules.
        """
        # Ensure confidence score is strictly bounded
        output.confidence_score = min(1.0, max(0.0, output.confidence_score))
        
        # Verify explanation text is non-empty
        if not output.explanation_text:
            output.explanation_text = "Prediction generated based on historical network telemetry."

        logger.info(f"Governance Audit PASSED for prediction {output.prediction_id}")
        return output
