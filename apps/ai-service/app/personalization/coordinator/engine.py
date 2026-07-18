# app/personalization/coordinator/engine.py
from datetime import datetime
import logging
import uuid
from typing import Dict, Any
from app.personalization.interfaces.contracts import (
    IPersonalizationCoordinator,
    IPersonalizationContextFactory,
    IPipelineOrchestrator,
)
from app.personalization.dto.models import (
    TravelerPersonalizationContext,
    AIReadyPersonalizationContext,
)
from app.personalization.errors import ProfileUnavailable, MissingConsent

logger = logging.getLogger(__name__)


class PersonalizationCoordinator(IPersonalizationCoordinator):
    def __init__(
        self,
        context_factory: IPersonalizationContextFactory,
        pipeline_orchestrator: IPipelineOrchestrator,
    ) -> None:
        self._context_factory = context_factory
        self._pipeline_orchestrator = pipeline_orchestrator

    async def execute(
        self,
        traveler_id: str,
        request_type: str,
        raw_dto: Dict[str, Any],
        correlation_id: str,
    ) -> AIReadyPersonalizationContext:
        logger.info(
            "Coordinating personalization for traveler=%s request_type=%s",
            traveler_id,
            request_type,
        )

        try:
            context = await self._context_factory.build(traveler_id, correlation_id)
            return await self._pipeline_orchestrator.execute(context, raw_dto)

        except (ProfileUnavailable, MissingConsent) as e:
            logger.warning(
                "Graceful degradation triggered for traveler=%s: %s",
                traveler_id,
                e.__class__.__name__,
            )
            fallback_context = TravelerPersonalizationContext(
                traveler_id=traveler_id,
                version=1,
                correlation_id=correlation_id,
                timestamp=datetime.utcnow(),
                persona="GENERAL",
                explicit_preferences={},
                implicit_preferences={},
                active_patterns=[],
                active_intent={},
                confidence_scores={},
                evidence_references={},
                explanation_context={},
                audit_signature="sig-degraded",
                telemetry={"fallback_reason": e.__class__.__name__},
            )

            return AIReadyPersonalizationContext(
                personalization_context_id=f"ctx-degraded-{uuid.uuid4().hex[:8]}",
                context=fallback_context,
                explanations=[
                    {
                        "explanation": "Default settings applied due to profile constraints.",
                        "locale": "en-US",
                        "reason_code": "PREF_DEFAULT",
                        "evidence_id": "degraded",
                    }
                ],
                audit_token="degraded-token",
                timestamp=datetime.utcnow(),
            )
        except Exception as e:
            logger.error(
                "Coordination failure for traveler=%s: %s",
                traveler_id,
                e,
                exc_info=True,
            )
            fallback_context = TravelerPersonalizationContext(
                traveler_id=traveler_id,
                version=1,
                correlation_id=correlation_id,
                timestamp=datetime.utcnow(),
                persona="GENERAL",
                explicit_preferences={},
                implicit_preferences={},
                active_patterns=[],
                active_intent={},
                confidence_scores={},
                evidence_references={},
                explanation_context={},
                audit_signature="sig-error",
                telemetry={"fallback_reason": str(e)},
            )
            return AIReadyPersonalizationContext(
                personalization_context_id=f"ctx-error-{uuid.uuid4().hex[:8]}",
                context=fallback_context,
                explanations=[
                    {
                        "explanation": "Default settings applied.",
                        "locale": "en-US",
                        "reason_code": "PREF_DEFAULT",
                        "evidence_id": "error",
                    }
                ],
                audit_token="error-token",
                timestamp=datetime.utcnow(),
            )
