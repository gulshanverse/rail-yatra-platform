# app/personalization/dependency/engine.py
import logging
from datetime import datetime
from typing import List
import uuid
from app.personalization.interfaces.contracts import IPreferenceDependencyEngine
from app.personalization.dto.models import TravelerPreferenceDTO

logger = logging.getLogger(__name__)


class PreferenceDependencyEngine(IPreferenceDependencyEngine):
    def evaluate(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        logger.info(
            "Evaluating preference dependency rules across %d preferences",
            len(preferences),
        )

        existing_keys = {p.preference_key: p for p in preferences}
        evaluated_prefs = list(preferences)

        if (
            existing_keys.get("wheelchair_access")
            and existing_keys["wheelchair_access"].value is True
        ):
            seat_pref = existing_keys.get("seat_preference")
            if not seat_pref:
                lower_seat = TravelerPreferenceDTO(
                    preference_id=f"pref-dep-{uuid.uuid4().hex[:12]}",
                    traveler_profile_id=existing_keys[
                        "wheelchair_access"
                    ].traveler_profile_id,
                    category="COMFORT",
                    preference_key="seat_preference",
                    value="lower",
                    type="IMPLICIT",
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata={"dependency_source": "wheelchair_access"},
                )
                evaluated_prefs.append(lower_seat)
                logger.info(
                    "Added seat_preference=lower due to wheelchair_access dependency"
                )
            elif seat_pref.value != "lower":
                seat_pref.value = "lower"
                seat_pref.metadata["dependency_override"] = "wheelchair_access"
                logger.info(
                    "Overrode seat_preference to lower due to wheelchair_access dependency"
                )

        return evaluated_prefs
