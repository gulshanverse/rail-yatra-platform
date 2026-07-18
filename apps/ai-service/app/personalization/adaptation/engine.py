# app/personalization/adaptation/engine.py
from datetime import datetime
import logging
import uuid
from typing import Dict, Any
from app.personalization.interfaces.contracts import (
    IRecommendationAdaptationEngine,
    IReasonCodeEngine,
)
from app.personalization.dto.models import (
    TravelerPersonalizationContext,
    RecommendationAdaptationDTO,
)

logger = logging.getLogger(__name__)


class RecommendationAdaptationEngine(IRecommendationAdaptationEngine):
    def __init__(self, reason_code_engine: IReasonCodeEngine) -> None:
        self._reason_code_engine = reason_code_engine

    def adapt(
        self,
        raw_dto: Dict[str, Any],
        context: TravelerPersonalizationContext,
    ) -> RecommendationAdaptationDTO:
        scenario = raw_dto.get("scenario", "JOURNEY_LISTING")
        logger.info(
            "Adapting recommendation for traveler=%s scenario=%s",
            context.traveler_id,
            scenario,
        )

        target_id = raw_dto.get("id", f"rec-{uuid.uuid4().hex[:12]}")
        adapted_fields: Dict[str, Any] = {}
        matched_key = None
        matched_val = None
        matched_type = "EXPLICIT"

        if scenario == "JOURNEY_LISTING":
            pref_val = context.explicit_preferences.get("preferred_class")
            pref_type = "EXPLICIT"
            if not pref_val:
                pref_val = context.implicit_preferences.get("preferred_class")
                pref_type = "IMPLICIT"

            if pref_val:
                adapted_fields["preferred_class"] = pref_val
                matched_key = "preferred_class"
                matched_val = pref_val
                matched_type = pref_type
        elif scenario == "BOOKING_OPTIONS":
            pref_val = context.explicit_preferences.get("seat_preference")
            pref_type = "EXPLICIT"
            if not pref_val:
                pref_val = context.implicit_preferences.get("seat_preference")
                pref_type = "IMPLICIT"

            if pref_val:
                adapted_fields["seat_preference"] = pref_val
                matched_key = "seat_preference"
                matched_val = pref_val
                matched_type = pref_type
        else:
            pref_val = context.explicit_preferences.get("dietary_preference")
            pref_type = "EXPLICIT"
            if not pref_val:
                pref_val = context.implicit_preferences.get("dietary_preference")
                pref_type = "IMPLICIT"

            if pref_val:
                adapted_fields["dietary_preference"] = pref_val
                matched_key = "dietary_preference"
                matched_val = pref_val
                matched_type = pref_type

        reason_code_str = "PREF_DEFAULT"
        if matched_key:
            decision_context = {
                "preference_key": matched_key,
                "value": matched_val,
                "type": matched_type,
            }
            reason_dto = self._reason_code_engine.assign(decision_context)
            reason_code_str = reason_dto.code

        logger.info(
            "Adaptation complete: code=%s keys=%s",
            reason_code_str,
            list(adapted_fields.keys()),
        )
        return RecommendationAdaptationDTO(
            adaptation_id=f"adapt-{uuid.uuid4().hex[:12]}",
            target_id=target_id,
            adapted_fields=adapted_fields,
            reason_code=reason_code_str,
            timestamp=datetime.utcnow(),
        )
