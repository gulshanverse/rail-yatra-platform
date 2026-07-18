# app/personalization/observations/engine.py
from datetime import datetime, timedelta
import logging
import uuid
from typing import List, Dict, Any
from app.personalization.interfaces.contracts import (
    IObservationEngine,
    IObservationRepository,
)
from app.personalization.dto.models import LearningObservationDTO
from app.personalization.errors import InvalidObservation

logger = logging.getLogger(__name__)


class ObservationEngine(IObservationEngine):
    def __init__(self, observation_repository: IObservationRepository) -> None:
        self._obs_repo = observation_repository

    def ingest(
        self, traveler_id: str, action_type: str, value: Any
    ) -> LearningObservationDTO:
        if not traveler_id:
            raise InvalidObservation("traveler_id must not be empty.")
        if not action_type:
            raise InvalidObservation("action_type must not be empty.")

        logger.info(
            "Ingesting observation for traveler=%s type=%s", traveler_id, action_type
        )
        now = datetime.utcnow()
        obs = LearningObservationDTO(
            observation_id=f"obs-{uuid.uuid4().hex[:12]}",
            traveler_id=traveler_id,
            action_type=action_type,
            value=value,
            timestamp=now,
            ttl_expiry=now + timedelta(days=30),
            metadata={},
        )
        self._obs_repo.save(obs)
        return obs

    def batch_ingest(
        self, events: List[Dict[str, Any]]
    ) -> List[LearningObservationDTO]:
        logger.info("Batch ingesting %d events", len(events))
        results = []
        for event in events:
            traveler_id = event.get("traveler_id")
            action_type = event.get("action_type")
            value = event.get("value")

            try:
                obs = self.ingest(traveler_id, action_type, value)  # type: ignore
                results.append(obs)
            except Exception as e:
                logger.error("Failed to ingest event %s: %s", event, e)

        return results
