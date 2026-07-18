# app/personalization/behavior/engine.py
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any
from app.personalization.interfaces.contracts import (
    IBehaviorEngine,
    IBehaviorRepository,
    IObservationRepository,
)
from app.personalization.dto.models import (
    TravelerBehaviorDTO,
    TravelerPersonalizationContext,
)

logger = logging.getLogger(__name__)


class BehaviorEngine(IBehaviorEngine):
    def __init__(
        self,
        behavior_repository: IBehaviorRepository,
        observation_repository: IObservationRepository,
    ) -> None:
        self._behavior_repo = behavior_repository
        self._obs_repo = observation_repository

    def evaluate(self, context: TravelerPersonalizationContext) -> TravelerBehaviorDTO:
        traveler_id = context.traveler_id
        behavior = self._behavior_repo.get_by_traveler_id(traveler_id)
        if not behavior:
            logger.info(
                "No behavior found, returning default DTO for traveler=%s", traveler_id
            )
            behavior = TravelerBehaviorDTO(
                behavior_id=f"beh-{traveler_id}",
                traveler_profile_id=traveler_id,
                active_patterns=[],
                habits=[],
                routines=[],
                last_aggregation_date=datetime.utcnow(),
            )
        return behavior

    def detect_patterns(self, traveler_id: str) -> List[Dict[str, Any]]:
        logger.info("Detecting behavioral patterns for traveler=%s", traveler_id)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=30)
        observations = self._obs_repo.get_by_traveler_id_and_window(
            traveler_id, start_time, end_time
        )

        patterns = []

        # 1. Check for "budget_seeker" pattern: multiple searches for "SL" class
        sl_searches = [
            obs
            for obs in observations
            if obs.action_type == "SEARCH" and obs.value == "SL"
        ]
        if len(sl_searches) >= 3:
            patterns.append(
                {
                    "pattern": "budget_seeker",
                    "confidence": min(0.5 + 0.1 * len(sl_searches), 1.0),
                    "details": f"Detected {len(sl_searches)} searches for Sleeper class.",
                }
            )

        # 2. Check for "commuter" pattern: multiple bookings on weekdays
        weekday_bookings = [
            obs
            for obs in observations
            if obs.action_type == "BOOKING" and obs.timestamp.weekday() < 5
        ]
        if len(weekday_bookings) >= 3:
            patterns.append(
                {
                    "pattern": "weekly_commuter",
                    "confidence": min(0.6 + 0.08 * len(weekday_bookings), 1.0),
                    "details": f"Detected {len(weekday_bookings)} weekday bookings.",
                }
            )

        # 3. Check for "comfort_seeker" pattern: searches or bookings for "1A" class
        ac1_searches = [
            obs
            for obs in observations
            if obs.action_type in ("SEARCH", "BOOKING") and obs.value == "1A"
        ]
        if len(ac1_searches) >= 2:
            patterns.append(
                {
                    "pattern": "comfort_seeker",
                    "confidence": min(0.7 + 0.1 * len(ac1_searches), 1.0),
                    "details": f"Detected {len(ac1_searches)} actions for First Class AC.",
                }
            )

        logger.info("Detected %d patterns for traveler=%s", len(patterns), traveler_id)
        return patterns
