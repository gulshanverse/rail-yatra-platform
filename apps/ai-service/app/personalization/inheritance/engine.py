# app/personalization/inheritance/engine.py
import logging
from datetime import datetime
from typing import List
import uuid
from app.personalization.interfaces.contracts import IPreferenceInheritanceEngine
from app.personalization.dto.models import TravelerPreferenceDTO

logger = logging.getLogger(__name__)


class PreferenceInheritanceEngine(IPreferenceInheritanceEngine):
    def propagate(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        logger.info(
            "Propagating preference inheritance rules across %d preferences",
            len(preferences),
        )

        existing_keys = {p.preference_key: p for p in preferences}
        propagated_prefs = list(preferences)

        # 1. dietary_preference -> meal_choice
        if "dietary_preference" in existing_keys and "meal_choice" not in existing_keys:
            diet_pref = existing_keys["dietary_preference"]
            inherited = TravelerPreferenceDTO(
                preference_id=f"pref-inh-{uuid.uuid4().hex[:12]}",
                traveler_profile_id=diet_pref.traveler_profile_id,
                category="DIETARY",
                preference_key="meal_choice",
                value=diet_pref.value,
                type="IMPLICIT",
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={"inherited_from": "dietary_preference"},
            )
            propagated_prefs.append(inherited)
            logger.info(
                "Inherited meal_choice from dietary_preference with value=%s",
                diet_pref.value,
            )

        # 2. accessibility_needs -> wheelchair_access
        if (
            "accessibility_needs" in existing_keys
            and "wheelchair_access" not in existing_keys
        ):
            access_pref = existing_keys["accessibility_needs"]
            if access_pref.value in ("wheelchair", "WCHR", True):
                inherited = TravelerPreferenceDTO(
                    preference_id=f"pref-inh-{uuid.uuid4().hex[:12]}",
                    traveler_profile_id=access_pref.traveler_profile_id,
                    category="COMFORT",
                    preference_key="wheelchair_access",
                    value=True,
                    type="IMPLICIT",
                    version=1,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    metadata={"inherited_from": "accessibility_needs"},
                )
                propagated_prefs.append(inherited)
                logger.info("Inherited wheelchair_access from accessibility_needs")

        return propagated_prefs
