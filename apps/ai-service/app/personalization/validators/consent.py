# app/personalization/validators/consent.py
from app.personalization.interfaces.contracts import (
    IConsentValidator,
    ITravelerProfileRepository,
)


class ConsentValidator(IConsentValidator):
    def __init__(self, profile_repository: ITravelerProfileRepository) -> None:
        self._profile_repo = profile_repository

    def validate_consent(self, traveler_id: str) -> bool:
        if not traveler_id:
            return False
        profile = self._profile_repo.get_by_traveler_id(traveler_id)
        if not profile:
            return False
        # Checking consent flag in metadata or metadata mapping
        consent = profile.get("consent_granted", False)
        # Or look in profile metadata dictionary
        if not consent and "metadata" in profile:
            consent = profile["metadata"].get("consent_granted", False)
        return bool(consent)
