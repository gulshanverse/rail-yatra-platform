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
    ReasonCodeDTO,
    PreferenceEvidenceDTO,
    PreferenceAuditDTO,
)
from app.personalization.cache import CacheManager
from app.personalization.preferences import PreferenceEngine
from app.personalization.behavior import BehaviorEngine
from app.personalization.observations import ObservationEngine
from app.personalization.adaptation import RecommendationAdaptationEngine
from app.personalization.reason_codes import ReasonCodeEngine
from app.personalization.explanations import ExplanationEngine
from app.personalization.learning import LearningEngine
from app.personalization.confidence import ConfidenceEngine
from app.personalization.conflict import ConflictResolutionEngine
from app.personalization.inheritance import PreferenceInheritanceEngine
from app.personalization.dependency import PreferenceDependencyEngine
from app.personalization.audit import AuditEngine
from app.personalization.metrics import MetricsEngine
from app.personalization.health import HealthEngine
from app.personalization.pipeline import PipelineOrchestrator
from app.personalization.coordinator import PersonalizationCoordinator
from app.personalization.gateway import PersonalizationGateway
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


class TestPersonalizationBatch3(unittest.TestCase):
    def setUp(self) -> None:
        self.learning_engine = LearningEngine()
        self.confidence_engine = ConfidenceEngine()
        self.conflict_engine = ConflictResolutionEngine()
        self.inheritance_engine = PreferenceInheritanceEngine()
        self.dependency_engine = PreferenceDependencyEngine()

    def test_learning_engine(self) -> None:
        obs_list = [
            LearningObservationDTO(
                observation_id=f"obs-{i}",
                traveler_id="traveler-b3-1",
                action_type="SEARCH",
                value="SL",
                timestamp=datetime.utcnow(),
                ttl_expiry=datetime.utcnow(),
                metadata={},
            )
            for i in range(5)
        ]
        behavior = TravelerBehaviorDTO(
            behavior_id="beh-b3-1",
            traveler_profile_id="traveler-b3-1",
            active_patterns=[],
            habits=[],
            routines=[],
            last_aggregation_date=datetime.utcnow(),
        )
        decisions = self.learning_engine.evaluate(obs_list, behavior)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0].mutation_key, "preferred_class")
        self.assertEqual(decisions[0].mutation_value, "SL")
        self.assertEqual(decisions[0].mutation_category, "COMFORT")
        self.assertTrue(decisions[0].confidence_score >= 0.5)

    def test_confidence_engine(self) -> None:
        # 1. Base calculate
        last_observed = datetime.utcnow()
        conf = self.confidence_engine.calculate("pref-b3-1", 3, last_observed)
        # score = 0.5 + 3 * 0.1 = 0.8
        self.assertEqual(conf.score, 0.8)
        self.assertEqual(conf.level, "HIGH")

        # 2. Decay calculate (10 days elapsed)
        ten_days_ago = datetime.utcnow() - timedelta(days=10)
        conf_decayed = self.confidence_engine.calculate("pref-b3-1", 3, ten_days_ago)
        # score = 0.8 * (0.95 ** 10) = 0.8 * 0.5987 = 0.479
        self.assertAlmostEqual(conf_decayed.score, 0.8 * (0.95**10), places=5)
        self.assertEqual(conf_decayed.level, "MEDIUM")

        # 3. apply_decay method
        conf.last_evaluated = datetime.utcnow() - timedelta(days=5)
        conf_applied = self.confidence_engine.apply_decay(conf)
        self.assertAlmostEqual(conf_applied.score, 0.8 * (0.95**5), places=5)

    def test_conflict_engine(self) -> None:
        p_explicit = TravelerPreferenceDTO(
            preference_id="p-e",
            traveler_profile_id="traveler-b3-2",
            category="COMFORT",
            preference_key="preferred_class",
            value="2A",
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        p_implicit = TravelerPreferenceDTO(
            preference_id="p-i",
            traveler_profile_id="traveler-b3-2",
            category="COMFORT",
            preference_key="preferred_class",
            value="3A",
            type="IMPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"confidence_score": 0.9},
        )
        p_implicit_low = TravelerPreferenceDTO(
            preference_id="p-i-low",
            traveler_profile_id="traveler-b3-2",
            category="COMFORT",
            preference_key="preferred_class",
            value="SL",
            type="IMPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={"confidence_score": 0.4},
        )

        # Explicit vs Implicit resolution
        resolved = self.conflict_engine.resolve([p_explicit, p_implicit])
        self.assertEqual(len(resolved), 1)
        self.assertEqual(resolved[0].value, "2A")  # Explicit wins

        # Multiple implicit resolution
        resolved_implicit = self.conflict_engine.resolve([p_implicit, p_implicit_low])
        self.assertEqual(len(resolved_implicit), 1)
        self.assertEqual(
            resolved_implicit[0].value, "3A"
        )  # Highest confidence score wins

        # Detect conflicts
        conflicts = self.conflict_engine.detect_conflicts([p_explicit, p_implicit])
        self.assertEqual(len(conflicts), 1)
        self.assertEqual(conflicts[0]["conflict_type"], "EXPLICIT_IMPLICIT_OVERRIDE")

    def test_inheritance_engine(self) -> None:
        dietary_pref = TravelerPreferenceDTO(
            preference_id="p-diet",
            traveler_profile_id="traveler-b3-3",
            category="DIETARY",
            preference_key="dietary_preference",
            value="veg",
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        propagated = self.inheritance_engine.propagate([dietary_pref])
        self.assertEqual(len(propagated), 2)
        meal_choice = [p for p in propagated if p.preference_key == "meal_choice"][0]
        self.assertEqual(meal_choice.value, "veg")

    def test_dependency_engine(self) -> None:
        wheelchair_pref = TravelerPreferenceDTO(
            preference_id="p-wheel",
            traveler_profile_id="traveler-b3-4",
            category="COMFORT",
            preference_key="wheelchair_access",
            value=True,
            type="EXPLICIT",
            version=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            metadata={},
        )
        evaluated = self.dependency_engine.evaluate([wheelchair_pref])
        self.assertEqual(len(evaluated), 2)
        seat_pref = [p for p in evaluated if p.preference_key == "seat_preference"][0]
        self.assertEqual(seat_pref.value, "lower")


class TestPersonalizationBatch4(unittest.TestCase):
    def setUp(self) -> None:
        self.reason_code_engine = ReasonCodeEngine()
        self.explanation_engine = ExplanationEngine()
        self.adaptation_engine = RecommendationAdaptationEngine(self.reason_code_engine)

    def test_reason_code_engine(self) -> None:
        reason_exp = self.reason_code_engine.assign(
            {"preference_key": "preferred_class", "type": "EXPLICIT"}
        )
        self.assertEqual(reason_exp.code, "PREF_EXPLICIT_CLASS")
        self.assertEqual(reason_exp.priority, 10)

        reason_imp = self.reason_code_engine.assign(
            {"preference_key": "seat_preference", "type": "IMPLICIT"}
        )
        self.assertEqual(reason_imp.code, "PREF_IMPLICIT_SEAT")
        self.assertEqual(reason_imp.priority, 4)

        reason_lookup = self.reason_code_engine.lookup("PREF_EXPLICIT_CLASS")
        self.assertEqual(reason_lookup.code, "PREF_EXPLICIT_CLASS")

    def test_explanation_engine(self) -> None:
        reason = ReasonCodeDTO(
            code="PREF_EXPLICIT_CLASS",
            category="COMFORT",
            description="Personalized comfort options",
            priority=10,
            explanation_template="Personalized comfort class preference of {value}.",
        )
        evidence = PreferenceEvidenceDTO(
            evidence_id="ev-1",
            preference_id="pref-1",
            observation_ids=[],
            rule_triggers=[],
            timestamp=datetime.utcnow(),
        )
        res = self.explanation_engine.explain(reason, evidence, "en-US")
        self.assertEqual(
            res["explanation"],
            "Personalized comfort class preference of active choice.",
        )
        self.assertEqual(res["locale"], "en-US")
        self.assertEqual(res["reason_code"], "PREF_EXPLICIT_CLASS")

    def test_recommendation_adaptation_engine(self) -> None:
        ctx = TravelerPersonalizationContext(
            traveler_id="traveler-b4",
            version=1,
            correlation_id="corr-b4",
            timestamp=datetime.utcnow(),
            persona="GENERAL",
            explicit_preferences={"preferred_class": "2A"},
            implicit_preferences={"seat_preference": "lower"},
            active_patterns=[],
            active_intent={},
            confidence_scores={},
            evidence_references={},
            explanation_context={},
            audit_signature="sig-b4",
            telemetry={},
        )
        rec_journey = {
            "id": "rec-123",
            "name": "Journey Offer",
            "scenario": "JOURNEY_LISTING",
        }
        rec_booking = {
            "id": "rec-123",
            "name": "Seat Offer",
            "scenario": "BOOKING_OPTIONS",
        }

        # Journey listing scenario (uses class)
        adapt_journey = self.adaptation_engine.adapt(rec_journey, ctx)
        self.assertEqual(adapt_journey.target_id, "rec-123")
        self.assertEqual(adapt_journey.adapted_fields.get("preferred_class"), "2A")
        self.assertEqual(adapt_journey.reason_code, "PREF_EXPLICIT_CLASS")

        # Booking options scenario (uses seat)
        adapt_booking = self.adaptation_engine.adapt(rec_booking, ctx)
        self.assertEqual(adapt_booking.adapted_fields.get("seat_preference"), "lower")
        self.assertEqual(adapt_booking.reason_code, "PREF_IMPLICIT_SEAT")


class TestPersonalizationBatch5(unittest.TestCase):
    def setUp(self) -> None:
        self.profile_repo = InMemoryProfileRepository()
        self.preference_repo = InMemoryPreferenceRepository()
        self.behavior_repo = InMemoryBehaviorRepository()
        self.confidence_repo = InMemoryConfidenceRepository()
        self.audit_repo = InMemoryAuditRepository()
        self.metrics_repo = InMemoryMetricsRepository()
        self.observation_repo = InMemoryObservationRepository()

        self.profile_validator = ProfileValidator(self.profile_repo)
        self.consent_validator = ConsentValidator(self.profile_repo)
        self.context_factory = TravelerPersonalizationContextFactory(
            profile_repository=self.profile_repo,
            preference_repository=self.preference_repo,
            behavior_repository=self.behavior_repo,
            confidence_repository=self.confidence_repo,
            profile_validator=self.profile_validator,
            consent_validator=self.consent_validator,
        )

        self.reason_code_engine = ReasonCodeEngine()
        self.explanation_engine = ExplanationEngine()
        self.adaptation_engine = RecommendationAdaptationEngine(self.reason_code_engine)
        self.audit_engine = AuditEngine(self.audit_repo)
        self.metrics_engine = MetricsEngine(self.metrics_repo)
        self.health_engine = HealthEngine()
        self.observation_engine = ObservationEngine(self.observation_repo)

        self.pipeline_orchestrator = PipelineOrchestrator(
            adaptation_engine=self.adaptation_engine,
            reason_code_engine=self.reason_code_engine,
            explanation_engine=self.explanation_engine,
            audit_engine=self.audit_engine,
            metrics_engine=self.metrics_engine,
        )

        self.coordinator = PersonalizationCoordinator(
            context_factory=self.context_factory,
            pipeline_orchestrator=self.pipeline_orchestrator,
        )

        self.gateway = PersonalizationGateway(
            coordinator=self.coordinator,
            observation_engine=self.observation_engine,
            health_engine=self.health_engine,
        )

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self) -> None:
        self.loop.close()

    def test_audit_engine(self) -> None:
        audit = PreferenceAuditDTO(
            audit_id="aud-test-1",
            correlation_id="corr-1",
            timestamp=datetime.utcnow(),
            traveler_id="traveler-1",
            action="TEST",
            change_log={},
            policy_applied="test",
            cryptographic_hash="sig-test",
        )
        self.audit_engine.log(audit)
        self.assertTrue(self.audit_engine.verify("aud-test-1"))
        self.assertFalse(self.audit_engine.verify("non-existent"))

    def test_metrics_engine(self) -> None:
        self.metrics_engine.increment("test.metric", {"tag": "val"})
        self.metrics_engine.observe("test.latency", 45.2, {"tag": "val"})
        self.assertEqual(len(self.metrics_repo._metrics), 2)

    def test_health_engine(self) -> None:
        res = self.health_engine.check()
        self.assertEqual(res["status"], "UP")
        self.assertEqual(self.health_engine.check_subsystem("sub")["status"], "UP")

    def test_gateway_flow(self) -> None:
        async def run_test() -> None:
            self.profile_repo.create_profile("traveler-b5-1", "hash-b5")

            pref = TravelerPreferenceDTO(
                preference_id="pref-b5-1",
                traveler_profile_id="traveler-b5-1",
                category="COMFORT",
                preference_key="preferred_class",
                value="3A",
                type="EXPLICIT",
                version=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                metadata={},
            )
            self.preference_repo.save(pref)

            await self.gateway.ingest_observation(
                "traveler-b5-1", "SEARCH", "3A", "corr-b5"
            )
            self.assertEqual(len(self.observation_repo._observations), 1)

            rec_dto = {"id": "rec-99", "scenario": "JOURNEY_LISTING"}
            result = await self.gateway.personalize(
                traveler_id="traveler-b5-1",
                request_type="JOURNEY_LISTING",
                raw_dto=rec_dto,
                correlation_id="corr-b5",
            )
            self.assertEqual(result.context.traveler_id, "traveler-b5-1")
            self.assertEqual(len(result.explanations), 1)
            self.assertEqual(
                result.explanations[0]["reason_code"], "PREF_EXPLICIT_CLASS"
            )

            health = self.gateway.health_check()
            self.assertEqual(health["status"], "UP")

        self.loop.run_until_complete(run_test())

    def test_coordinator_graceful_fallback(self) -> None:
        async def run_test() -> None:
            rec_dto = {"id": "rec-99", "scenario": "JOURNEY_LISTING"}
            result = await self.gateway.personalize(
                traveler_id="traveler-non-existent",
                request_type="JOURNEY_LISTING",
                raw_dto=rec_dto,
                correlation_id="corr-b5-err",
            )
            self.assertEqual(result.context.traveler_id, "traveler-non-existent")
            self.assertEqual(result.explanations[0]["reason_code"], "PREF_DEFAULT")
            self.assertEqual(result.audit_token, "degraded-token")

            self.profile_repo.create_profile("traveler-revoked", "hash-revoked")
            prof = self.profile_repo.get_by_traveler_id("traveler-revoked")
            prof["consent_granted"] = False
            prof["metadata"]["consent_granted"] = False

            result_revoked = await self.gateway.personalize(
                traveler_id="traveler-revoked",
                request_type="JOURNEY_LISTING",
                raw_dto=rec_dto,
                correlation_id="corr-b5-rev",
            )
            self.assertEqual(result_revoked.context.traveler_id, "traveler-revoked")
            self.assertEqual(
                result_revoked.explanations[0]["reason_code"], "PREF_DEFAULT"
            )
            self.assertEqual(result_revoked.audit_token, "degraded-token")

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
