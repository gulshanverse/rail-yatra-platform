# app/personalization/repositories/profile_repository.py
import logging
from typing import Dict, Any, Optional
from app.personalization.interfaces.contracts import ITravelerProfileRepository

logger = logging.getLogger(__name__)


class InMemoryProfileRepository(ITravelerProfileRepository):
    """In-memory implementation of the traveler profile repository."""

    def __init__(self) -> None:
        self._profiles: Dict[str, Dict[str, Any]] = {}

    def get_by_traveler_id(self, traveler_id: str) -> Optional[Dict[str, Any]]:
        return self._profiles.get(traveler_id)

    def create_profile(self, traveler_id: str, identity_hash: str) -> Dict[str, Any]:
        profile: Dict[str, Any] = {
            "traveler_id": traveler_id,
            "identity_hash": identity_hash,
            "version": 1,
            "consent_granted": True,
            "persona": "GENERAL",
            "metadata": {
                "consent_granted": True,
            },
        }
        self._profiles[traveler_id] = profile
        logger.info("Profile created for traveler_id=%s", traveler_id)
        return profile

    def delete_profile(self, traveler_id: str) -> bool:
        if traveler_id in self._profiles:
            del self._profiles[traveler_id]
            logger.info("Profile deleted for traveler_id=%s", traveler_id)
            return True
        return False
