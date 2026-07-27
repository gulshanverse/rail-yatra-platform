"""
Personalized Decision Support Engine (FR-8, Passenger Domain).
"""

import logging
from app.predictive.interfaces import (
    PassengerProfileContext,
    RiskEvaluation,
    AlternativeJourneyRecommendation,
    RiskLevel,
)

logger = logging.getLogger("ai-service.predictive.personalization")


class PersonalizedDecisionSupportEngine:
    """
    Engine for personalizing risk limits and ranking alternatives according to traveler profiles (FR-8).
    """

    async def personalize_decision_support(
        self,
        passenger: PassengerProfileContext,
        risk: RiskEvaluation,
        recommendation: AlternativeJourneyRecommendation,
    ) -> AlternativeJourneyRecommendation:
        # Re-score alternatives based on passenger risk tolerance
        risk_tol = passenger.risk_tolerance

        boost_map = {
            RiskLevel.LOW: 1.2,     # Risk-averse traveler prefers highest probability
            RiskLevel.MEDIUM: 1.0,  # Balanced traveler
            RiskLevel.HIGH: 0.8,    # Risk-tolerant traveler prefers speed
            RiskLevel.CRITICAL: 0.7,
        }
        multiplier = boost_map.get(risk_tol, 1.0)

        for alt in recommendation.recommended_alternatives:
            # Adjust match score based on risk tolerance profile
            adjusted_score = alt.match_score * (alt.confirmation_probability / 100.0) * multiplier
            alt.match_score = round(min(1.0, max(0.1, adjusted_score)), 2)

        # Sort with updated personalized scores
        recommendation.recommended_alternatives.sort(key=lambda x: x.match_score, reverse=True)

        logger.info(
            f"Personalized Decision Support for traveler {passenger.traveler_id} (Risk Tol: {risk_tol.value})"
        )

        return recommendation
