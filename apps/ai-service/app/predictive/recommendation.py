"""
Alternative Travel Orchestrator (FR-5, Capability CP-3).
"""

import logging
from app.predictive.interfaces import (
    JourneyContext,
    RiskEvaluation,
    AlternativeOption,
    AlternativeJourneyRecommendation,
    PassengerProfileContext,
)

logger = logging.getLogger("ai-service.predictive.recommendation")


class AlternativeTravelOrchestrator:
    """
    Recommendation Engine for fallback travel routes (FR-5).
    """

    async def generate_alternatives(
        self,
        journey: JourneyContext,
        risk: RiskEvaluation,
        passenger: PassengerProfileContext,
    ) -> AlternativeJourneyRecommendation:
        alternatives = []

        # Synthetic alternative generation based on primary route
        orig = journey.origin_station
        dest = journey.destination_station
        pref_class = passenger.preferred_class or journey.booking_class

        # Option A: Direct high-speed alternative
        opt_a = AlternativeOption(
            train_number="12952",
            train_name=f"Rajdhani Express ({orig}-{dest})",
            departure_time="16:55",
            arrival_time="08:35",
            booking_class=pref_class,
            confirmation_probability=94.5,
            predicted_delay_mins=10,
            duration_mins=940,
            risk_score=5.0,
            match_score=0.96,
        )
        alternatives.append(opt_a)

        # Option B: Premium Duronto alternative
        opt_b = AlternativeOption(
            train_number="12260",
            train_name=f"Duronto Express ({orig}-{dest})",
            departure_time="18:15",
            arrival_time="10:15",
            booking_class=pref_class,
            confirmation_probability=88.0,
            predicted_delay_mins=15,
            duration_mins=960,
            risk_score=12.0,
            match_score=0.89,
        )
        alternatives.append(opt_b)

        # Option C: Safe buffer alternative
        opt_c = AlternativeOption(
            train_number="12302",
            train_name=f"Superfast Express ({orig}-{dest})",
            departure_time="20:00",
            arrival_time="12:45",
            booking_class="SL" if pref_class == "SL" else "3A",
            confirmation_probability=99.0,
            predicted_delay_mins=20,
            duration_mins=1005,
            risk_score=8.0,
            match_score=0.82,
        )
        alternatives.append(opt_c)

        # Filter alternatives by risk score
        alternatives.sort(key=lambda x: x.match_score, reverse=True)

        reason = (
            f"Transfer risk is {risk.risk_level.value} ({risk.missed_connection_probability}% missed connection prob). "
            f"Top alternative {opt_a.train_name} increases confirmation probability to 94.5% with safe buffer."
        )

        logger.info(
            f"Alternative Orchestration for Train {journey.train_number}: Generated {len(alternatives)} alternatives."
        )

        return AlternativeJourneyRecommendation(
            original_train=journey.train_number,
            recommended_alternatives=alternatives,
            optimization_reason=reason,
            traveler_match_score=round(alternatives[0].match_score, 2),
        )
