# app/personalization/context/factory.py
from datetime import datetime
import logging
from app.personalization.interfaces.contracts import (
    IPersonalizationContextFactory,
    ITravelerProfileRepository,
    IPreferenceRepository,
    IBehaviorRepository,
    IConfidenceRepository,
    IProfileValidator,
    IConsentValidator,
)
from app.personalization.dto.models import TravelerPersonalizationContext
from app.personalization.errors import ProfileUnavailable, MissingConsent

logger = logging.getLogger(__name__)


class TravelerPersonalizationContextFactory(IPersonalizationContextFactory):
    def __init__(
        self,
        profile_repository: ITravelerProfileRepository,
        preference_repository: IPreferenceRepository,
        behavior_repository: IBehaviorRepository,
        confidence_repository: IConfidenceRepository,
        profile_validator: IProfileValidator,
        consent_validator: IConsentValidator,
    ) -> None:
        self._profile_repo = profile_repository
        self._preference_repo = preference_repository
        self._behavior_repo = behavior_repository
        self._confidence_repo = confidence_repository
        self._profile_validator = profile_validator
        self._consent_validator = consent_validator

    async def build(
        self, traveler_id: str, correlation_id: str
    ) -> TravelerPersonalizationContext:
        logger.info(
            "Building context for traveler_id=%s, correlation_id=%s",
            traveler_id,
            correlation_id,
        )

        # Validate profile
        if not self._profile_validator.validate_profile(traveler_id):
            logger.error("Profile validation failed for traveler_id=%s", traveler_id)
            raise ProfileUnavailable(
                f"Profile not found or invalid for traveler_id={traveler_id}"
            )

        # Validate consent
        if not self._consent_validator.validate_consent(traveler_id):
            logger.error("Consent validation failed for traveler_id=%s", traveler_id)
            raise MissingConsent(
                f"Consent is missing or not granted for traveler_id={traveler_id}"
            )

        profile = self._profile_repo.get_by_traveler_id(traveler_id)
        if not profile:
            raise ProfileUnavailable(
                f"Profile not found or invalid for traveler_id={traveler_id}"
            )

        # Load preferences
        preferences = self._preference_repo.get_by_traveler_id(traveler_id)
        explicit = {}
        implicit = {}
        confidence_scores = {}
        evidence_references = {}

        for pref in preferences:
            if pref.type == "EXPLICIT":
                explicit[pref.preference_key] = pref.value
            elif pref.type == "IMPLICIT":
                implicit[pref.preference_key] = pref.value
                # Resolve confidence if implicit
                conf = self._confidence_repo.get_by_preference_id(pref.preference_id)
                if conf:
                    confidence_scores[pref.preference_key] = conf.score

            # Gather evidence keys if present
            if pref.metadata and "evidence_ids" in pref.metadata:
                evidence_references[pref.preference_key] = pref.metadata["evidence_ids"]

        # Load behavior
        behavior = self._behavior_repo.get_by_traveler_id(traveler_id)
        active_patterns = behavior.active_patterns if behavior else []

        # Build explanation context
        explanation_context = {}
        if profile.get("persona"):
            explanation_context["persona"] = profile["persona"]

        # Construct audit signature
        audit_sig = f"sig:{traveler_id}:{profile.get('version', 1)}:{correlation_id}"

        context = TravelerPersonalizationContext(
            traveler_id=traveler_id,
            version=profile.get("version", 1),
            correlation_id=correlation_id,
            timestamp=datetime.utcnow(),
            persona=profile.get("persona", "GENERAL"),
            explicit_preferences=explicit,
            implicit_preferences=implicit,
            active_patterns=active_patterns,
            active_intent=profile.get("metadata", {}).get("active_intent", {}),
            confidence_scores=confidence_scores,
            evidence_references=evidence_references,
            explanation_context=explanation_context,
            audit_signature=audit_sig,
            telemetry={},
        )
        return context
