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
    TravelerPersonalizationContext,
)
from app.personalization.cache import CacheManager
from app.personalization.preferences import PreferenceEngine
from app.personalization.behavior import BehaviorEngine
from app.personalization.observations import ObservationEngine
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


class TestPersonalizationBatch2(unittest.TestCase):
    def setUp(self) -> None:
        self.profile_repo = InMemoryProfileRepository()
        self.preference_repo = InMemoryPreferenceRepository()
        self.behavior_repo = InMemoryBehaviorRepository()
        self.observation_repo = InMemoryObservationRepository()
        self.confidence_repo = InMemoryConfidenceRepository()
        self.cache_repo = InMemoryCacheRepository()

        self.cache_manager = CacheManager(self.cache_repo)
        self.pref_engine = PreferenceEngine(self.preference_repo, self.cache_manager)
        self.behavior_engine = BehaviorEngine(self.behavior_repo, self.observation_repo)
        self.observation_engine = ObservationEngine(self.observation_repo)

    def test_cache_manager(self) -> None:
        self.cache_manager.put("test-cache", "key-1", "value-1", 60)
        self.assertEqual(self.cache_manager.get("test-cache", "key-1"), "value-1")

        self.cache_manager.invalidate("test-cache", "key-1")
        self.assertIsNone(self.cache_manager.get("test-cache", "key-1"))

        self.cache_manager.put("test-cache", "key-2", "value-2", 60)
        self.cache_manager.put("other-cache", "key-2", "value-other", 60)
        self.cache_manager.invalidate_all("test-cache")
        self.assertIsNone(self.cache_manager.get("test-cache", "key-2"))
        self.assertEqual(self.cache_manager.get("other-cache", "key-2"), "value-other")

    def test_preference_engine(self) -> None:
        # Resolve from empty DB
        ctx = TravelerPersonalizationContext(
            traveler_id="traveler-b2-1",
            version=1,
            correlation_id="corr-b2",
            timestamp=datetime.utcnow(),
            persona="GENERAL",
            explicit_preferences={},
            implicit_preferences={},
            active_patterns=[],
            active_intent={},
            confidence_scores={},
            evidence_references={},
            explanation_context={},
            audit_signature="sig-1",
            telemetry={},
        )
        prefs = self.pref_engine.resolve(ctx)
        self.assertEqual(len(prefs), 0)

        # Save and resolve
        pref1 = TravelerPreferenceDTO(
            preference_id="pref-b2-1",
            traveler_profile_id="traveler-b2-1",
            category="COMFORT",
            preference_key="seat_preference",
            value="lower",
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        pref2 = TravelerPreferenceDTO(
            preference_id="pref-b2-2",
            traveler_profile_id="traveler-b2-1",
            category="DIETARY",
            preference_key="meal_preference",
            value="veg",
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        self.pref_engine.update("traveler-b2-1", pref1)
        self.pref_engine.update("traveler-b2-1", pref2)

        resolved_prefs = self.pref_engine.resolve(ctx)
        self.assertEqual(len(resolved_prefs), 2)

        # Test partial reset (by category COMFORT)
        self.pref_engine.reset("traveler-b2-1", "COMFORT")
        resolved_after_partial = self.pref_engine.resolve(ctx)
        # Should only have DIETARY preference remaining
        self.assertEqual(len(resolved_after_partial), 1)
        self.assertEqual(resolved_after_partial[0].category, "DIETARY")

        # Test full reset
        self.pref_engine.reset("traveler-b2-1")
        self.assertEqual(len(self.pref_engine.resolve(ctx)), 0)

    def test_behavior_engine_and_pattern_detection(self) -> None:
        ctx = TravelerPersonalizationContext(
            traveler_id="traveler-b2-2",
            version=1,
            correlation_id="corr-b2",
            timestamp=datetime.utcnow(),
            persona="GENERAL",
            explicit_preferences={},
            implicit_preferences={},
            active_patterns=[],
            active_intent={},
            confidence_scores={},
            evidence_references={},
            explanation_context={},
            audit_signature="sig-2",
            telemetry={},
        )
        # Test evaluate default DTO
        behavior = self.behavior_engine.evaluate(ctx)
        self.assertEqual(behavior.traveler_profile_id, "traveler-b2-2")
        self.assertEqual(len(behavior.active_patterns), 0)

        # Save and evaluate behavior DTO
        behavior.active_patterns = [{"pattern": "commuter"}]
        self.behavior_repo.save(behavior)
        behavior_res = self.behavior_engine.evaluate(ctx)
        self.assertEqual(len(behavior_res.active_patterns), 1)

        # Ingest observations to trigger pattern detection
        # 1. 3 searches for "SL" -> budget_seeker
        self.observation_engine.ingest("traveler-b2-2", "SEARCH", "SL")
        self.observation_engine.ingest("traveler-b2-2", "SEARCH", "SL")
        self.observation_engine.ingest("traveler-b2-2", "SEARCH", "SL")

        # 2. 3 bookings on weekdays -> weekly_commuter
        # Let's create weekday timestamp (Monday is weekday 0)
        weekday_dt = datetime.utcnow() - timedelta(days=1)
        while weekday_dt.weekday() >= 5:
            weekday_dt -= timedelta(days=1)
        obs_c1 = LearningObservationDTO(
            observation_id="obs-c1",
            traveler_id="traveler-b2-2",
            action_type="BOOKING",
            value="NDLS-BPL",
            timestamp=weekday_dt,
            ttl_expiry=weekday_dt + timedelta(days=30),
            metadata={},
        )
        obs_c2 = LearningObservationDTO(
            observation_id="obs-c2",
            traveler_id="traveler-b2-2",
            action_type="BOOKING",
            value="NDLS-BPL",
            timestamp=weekday_dt,
            ttl_expiry=weekday_dt + timedelta(days=30),
            metadata={},
        )
        obs_c3 = LearningObservationDTO(
            observation_id="obs-c3",
            traveler_id="traveler-b2-2",
            action_type="BOOKING",
            value="NDLS-BPL",
            timestamp=weekday_dt,
            ttl_expiry=weekday_dt + timedelta(days=30),
            metadata={},
        )
        self.observation_repo.save(obs_c1)
        self.observation_repo.save(obs_c2)
        self.observation_repo.save(obs_c3)

        detected = self.behavior_engine.detect_patterns("traveler-b2-2")
        detected_names = [p["pattern"] for p in detected]
        self.assertIn("budget_seeker", detected_names)
        self.assertIn("weekly_commuter", detected_names)

    def test_observation_engine_batch_ingest(self) -> None:
        events = [
            {"traveler_id": "traveler-b2-3", "action_type": "SEARCH", "value": "2A"},
            {"traveler_id": "traveler-b2-3", "action_type": "SEARCH", "value": "3A"},
            {"traveler_id": "", "action_type": "SEARCH", "value": "1A"},  # Invalid
        ]
        results = self.observation_engine.batch_ingest(events)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].traveler_id, "traveler-b2-3")
        self.assertEqual(results[0].action_type, "SEARCH")
        self.assertEqual(results[0].value, "2A")
        # Check generated id prefix
        self.assertTrue(results[0].observation_id.startswith("obs-"))


if __name__ == "__main__":
    unittest.main()
