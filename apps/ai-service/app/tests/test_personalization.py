# app/tests/test_personalization.py
import unittest
import asyncio
from datetime import datetime, timedelta

from app.personalization.repositories import (
    InMemoryProfileRepository,
    InMemoryPreferenceRepository,
    InMemoryBehaviorRepository,
    InMemoryObservationRepository,
    InMemoryConfidenceRepository,
    InMemoryReasonCodeRepository,
    InMemoryPolicyRepository,
    InMemoryConfigurationRepository,
    InMemoryAuditRepository,
    InMemoryMetricsRepository,
    InMemoryCacheRepository,
    LoggingEventPublisher,
)
from app.personalization.dto.models import (
    TravelerPreferenceDTO,
    TravelerBehaviorDTO,
    LearningObservationDTO,
    PreferenceConfidenceDTO,
)
from app.personalization.validators import (
    ProfileValidator,
    ConsentValidator,
    ContextValidator,
)
from app.personalization.context.factory import TravelerPersonalizationContextFactory
from app.personalization.errors import ProfileUnavailable, MissingConsent


class TestPersonalizationBatch1(unittest.TestCase):
    def setUp(self) -> None:
        self.profile_repo = InMemoryProfileRepository()
        self.preference_repo = InMemoryPreferenceRepository()
        self.behavior_repo = InMemoryBehaviorRepository()
        self.observation_repo = InMemoryObservationRepository()
        self.confidence_repo = InMemoryConfidenceRepository()
        self.reason_code_repo = InMemoryReasonCodeRepository()
        self.policy_repo = InMemoryPolicyRepository()
        self.config_repo = InMemoryConfigurationRepository()
        self.audit_repo = InMemoryAuditRepository()
        self.metrics_repo = InMemoryMetricsRepository()
        self.cache_repo = InMemoryCacheRepository()
        self.publisher = LoggingEventPublisher()

        self.profile_validator = ProfileValidator(self.profile_repo)
        self.consent_validator = ConsentValidator(self.profile_repo)
        self.context_validator = ContextValidator()

        self.factory = TravelerPersonalizationContextFactory(
            profile_repository=self.profile_repo,
            preference_repository=self.preference_repo,
            behavior_repository=self.behavior_repo,
            confidence_repository=self.confidence_repo,
            profile_validator=self.profile_validator,
            consent_validator=self.consent_validator,
        )

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_repositories_basic_flow(self) -> None:
        # 1. Profile repo
        profile = self.profile_repo.create_profile("traveler-1", "identity-hash-1")
        self.assertEqual(profile["traveler_id"], "traveler-1")
        self.assertTrue(profile["consent_granted"])

        resolved_profile = self.profile_repo.get_by_traveler_id("traveler-1")
        self.assertIsNotNone(resolved_profile)
        self.assertEqual(resolved_profile["identity_hash"], "identity-hash-1")

        # 2. Preference repo
        pref = TravelerPreferenceDTO(
            preference_id="pref-1",
            traveler_profile_id="traveler-1",
            category="COMFORT",
            preference_key="preferred_class",
            value="1A",
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        self.preference_repo.save(pref)
        prefs = self.preference_repo.get_by_traveler_id("traveler-1")
        self.assertEqual(len(prefs), 1)
        self.assertEqual(prefs[0].value, "1A")

        # 3. Behavior repo
        behavior = TravelerBehaviorDTO(
            behavior_id="beh-1",
            traveler_profile_id="traveler-1",
            active_patterns=[{"pattern": "weekly_commuter"}],
            habits=[],
            routines=[],
            last_aggregation_date=datetime.utcnow(),
        )
        self.behavior_repo.save(behavior)
        resolved_beh = self.behavior_repo.get_by_traveler_id("traveler-1")
        self.assertIsNotNone(resolved_beh)
        self.assertEqual(len(resolved_beh.active_patterns), 1)

        # 4. Observation repo
        obs = LearningObservationDTO(
            observation_id="obs-1",
            traveler_id="traveler-1",
            action_type="SEARCH",
            value="2A",
            timestamp=datetime.utcnow(),
            ttl_expiry=datetime.utcnow() + timedelta(days=1),
            metadata={},
        )
        self.observation_repo.save(obs)
        res_obs = self.observation_repo.get_by_traveler_id_and_window(
            "traveler-1",
            datetime.utcnow() - timedelta(minutes=5),
            datetime.utcnow() + timedelta(minutes=5),
        )
        self.assertEqual(len(res_obs), 1)

        # Expired sweep
        obs_expired = LearningObservationDTO(
            observation_id="obs-2",
            traveler_id="traveler-1",
            action_type="SEARCH",
            value="3A",
            timestamp=datetime.utcnow() - timedelta(days=2),
            ttl_expiry=datetime.utcnow() - timedelta(days=1),
            metadata={},
        )
        self.observation_repo.save(obs_expired)
        deleted = self.observation_repo.delete_expired()
        self.assertEqual(deleted, 1)

    def test_validators(self) -> None:
        # Invalid traveler profile validator
        self.assertFalse(self.profile_validator.validate_profile("non-existent"))
        self.assertFalse(self.consent_validator.validate_consent("non-existent"))

        # Valid profile
        self.profile_repo.create_profile("traveler-2", "hash-2")
        self.assertTrue(self.profile_validator.validate_profile("traveler-2"))
        self.assertTrue(self.consent_validator.validate_consent("traveler-2"))

        # Profile with revoked consent
        profile = self.profile_repo.get_by_traveler_id("traveler-2")
        profile["consent_granted"] = False
        profile["metadata"]["consent_granted"] = False
        self.assertFalse(self.consent_validator.validate_consent("traveler-2"))

    def test_context_factory(self) -> None:
        async def run_test() -> None:
            # Prepare profile, preference, behavior
            self.profile_repo.create_profile("traveler-3", "hash-3")

            pref_explicit = TravelerPreferenceDTO(
                preference_id="pref-3e",
                traveler_profile_id="traveler-3",
                category="COMFORT",
                preference_key="preferred_class",
                value="2A",
                type="EXPLICIT",
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            )
            pref_implicit = TravelerPreferenceDTO(
                preference_id="pref-3i",
                traveler_profile_id="traveler-3",
                category="COMFORT",
                preference_key="wheelchair_access",
                value=True,
                type="IMPLICIT",
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={"evidence_ids": ["obs-100"]},
            )
            self.preference_repo.save(pref_explicit)
            self.preference_repo.save(pref_implicit)

            conf = PreferenceConfidenceDTO(
                preference_id="pref-3i",
                score=0.85,
                level="HIGH",
                last_evaluated=datetime.utcnow(),
                decay_factor=0.05,
            )
            self.confidence_repo.save(conf)

            behavior = TravelerBehaviorDTO(
                behavior_id="beh-3",
                traveler_profile_id="traveler-3",
                active_patterns=[{"pattern": "frequent_traveler"}],
                habits=[],
                routines=[],
                last_aggregation_date=datetime.utcnow(),
            )
            self.behavior_repo.save(behavior)

            # Build context
            ctx = await self.factory.build("traveler-3", "corr-100")
            self.assertEqual(ctx.traveler_id, "traveler-3")
            self.assertEqual(ctx.explicit_preferences.get("preferred_class"), "2A")
            self.assertEqual(ctx.implicit_preferences.get("wheelchair_access"), True)
            self.assertEqual(ctx.confidence_scores.get("wheelchair_access"), 0.85)
            self.assertEqual(
                ctx.evidence_references.get("wheelchair_access"), ["obs-100"]
            )
            self.assertEqual(len(ctx.active_patterns), 1)

            # Test ProfileUnavailable
            with self.assertRaises(ProfileUnavailable):
                await self.factory.build("non-existent", "corr-200")

            # Test MissingConsent
            prof = self.profile_repo.get_by_traveler_id("traveler-3")
            prof["consent_granted"] = False
            prof["metadata"]["consent_granted"] = False
            with self.assertRaises(MissingConsent):
                await self.factory.build("traveler-3", "corr-300")

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
