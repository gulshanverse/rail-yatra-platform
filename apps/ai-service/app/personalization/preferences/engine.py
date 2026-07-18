# app/personalization/preferences/engine.py
import logging
from typing import List, Optional
from app.personalization.interfaces.contracts import (
    IPreferenceEngine,
    IPreferenceRepository,
    ICacheManager,
)
from app.personalization.dto.models import (
    TravelerPreferenceDTO,
    TravelerPersonalizationContext,
)

logger = logging.getLogger(__name__)


class PreferenceEngine(IPreferenceEngine):
    def __init__(
        self, preference_repository: IPreferenceRepository, cache_manager: ICacheManager
    ) -> None:
        self._pref_repo = preference_repository
        self._cache_manager = cache_manager

    def resolve(
        self, context: TravelerPersonalizationContext
    ) -> List[TravelerPreferenceDTO]:
        traveler_id = context.traveler_id
        # Try cache first
        cached = self._cache_manager.get("preferences", traveler_id)
        if cached is not None:
            logger.debug("Resolved preferences from cache for traveler=%s", traveler_id)
            return cached

        # Fetch from repository
        prefs = self._pref_repo.get_by_traveler_id(traveler_id)
        # Put in cache for 300 seconds
        self._cache_manager.put("preferences", traveler_id, prefs, 300)
        logger.info("Resolved preferences from repository for traveler=%s", traveler_id)
        return prefs

    def update(self, traveler_id: str, preference: TravelerPreferenceDTO) -> None:
        if preference.traveler_profile_id != traveler_id:
            logger.warning(
                "Traveler ID mismatch during update: profile=%s traveler=%s",
                preference.traveler_profile_id,
                traveler_id,
            )

        self._pref_repo.save(preference)
        self._cache_manager.invalidate("preferences", traveler_id)
        logger.info(
            "Updated preference for traveler=%s key=%s",
            traveler_id,
            preference.preference_key,
        )

    def reset(self, traveler_id: str, category: Optional[str] = None) -> None:
        if category:
            # Delete only preferences of target category
            prefs = self._pref_repo.get_by_traveler_id(traveler_id)
            non_matching = [p for p in prefs if p.category != category]
            self._pref_repo.delete_by_traveler_id(traveler_id)
            for p in non_matching:
                self._pref_repo.save(p)
            logger.info(
                "Reset preferences in category=%s for traveler=%s",
                category,
                traveler_id,
            )
        else:
            self._pref_repo.delete_by_traveler_id(traveler_id)
            logger.info("Reset all preferences for traveler=%s", traveler_id)

        self._cache_manager.invalidate("preferences", traveler_id)
