# app/personalization/gateway/engine.py
import logging
from typing import Dict, Any
from app.personalization.interfaces.contracts import (
    IPersonalizationGateway,
    IPersonalizationCoordinator,
    IObservationEngine,
    IHealthEngine,
)
from app.personalization.dto.models import AIReadyPersonalizationContext

logger = logging.getLogger(__name__)


class PersonalizationGateway(IPersonalizationGateway):
    def __init__(
        self,
        coordinator: IPersonalizationCoordinator,
        observation_engine: IObservationEngine,
        health_engine: IHealthEngine,
    ) -> None:
        self._coordinator = coordinator
        self._obs_engine = observation_engine
        self._health_engine = health_engine

    async def personalize(
        self,
        traveler_id: str,
        request_type: str,
        raw_dto: Dict[str, Any],
        correlation_id: str,
    ) -> AIReadyPersonalizationContext:
        logger.info(
            "Gateway personalize traveler=%s correlation=%s",
            traveler_id,
            correlation_id,
        )
        return await self._coordinator.execute(
            traveler_id=traveler_id,
            request_type=request_type,
            raw_dto=raw_dto,
            correlation_id=correlation_id,
        )

    async def ingest_observation(
        self,
        traveler_id: str,
        action_type: str,
        value: Any,
        correlation_id: str,
    ) -> None:
        logger.info(
            "Gateway ingest observation traveler=%s correlation=%s",
            traveler_id,
            correlation_id,
        )
        self._obs_engine.ingest(traveler_id, action_type, value)

    def health_check(self) -> Dict[str, Any]:
        logger.info("Gateway health check called")
        return self._health_engine.check()
