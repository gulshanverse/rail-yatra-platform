# app/personalization/validators/profile.py
from app.personalization.interfaces.contracts import (
    IProfileValidator,
    ITravelerProfileRepository,
)


class ProfileValidator(IProfileValidator):
    def __init__(self, profile_repository: ITravelerProfileRepository) -> None:
        self._profile_repo = profile_repository

    def validate_profile(self, traveler_id: str) -> bool:
        if not traveler_id or not isinstance(traveler_id, str):
            return False
        # In a real environment, we'd check length, prefix, characters, or repository
        profile = self._profile_repo.get_by_traveler_id(traveler_id)
        return profile is not None
