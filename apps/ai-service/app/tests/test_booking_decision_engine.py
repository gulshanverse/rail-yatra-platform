# app/tests/test_booking_decision_engine.py
import unittest
import asyncio
from app.booking.dto.models import BookingRequestDTO
from app.booking.gateway.coordinator import (
    BookingDecisionContextFactory,
    BookingCoordinator,
    BookingIntelligenceGateway,
)
from app.booking.candidate.builder import BookingCandidateBuilder
from app.booking.availability.engine import AvailabilityEngine
from app.booking.confirmation.engine import ConfirmationEngine
from app.booking.quota.engine import QuotaEngine
from app.booking.boarding.optimizer import BoardingEngine
from app.booking.constraints.engine import ConstraintEngine
from app.booking.risk.engine import RiskEngine
from app.booking.scoring.engine import ScoringEngine
from app.booking.strategy.registry import BookingStrategyRegistry
from app.booking.ranking.engine import RankingEngine
from app.booking.conflict.resolver import ConflictResolver
from app.booking.explanation.engine import ExplanationEngine
from app.booking.audit.logger import AuditEngine
from app.booking.metrics.collector import MetricsEngine
from app.booking.health.checker import HealthEngine
from app.booking.events.publisher import BookingEventPublisher


class TestBookingDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.candidate_builder = BookingCandidateBuilder()
        self.availability_engine = AvailabilityEngine()
        self.confirmation_engine = ConfirmationEngine()
        self.quota_engine = QuotaEngine()
        self.boarding_engine = BoardingEngine()
        self.constraint_engine = ConstraintEngine()
        self.risk_engine = RiskEngine()
        self.scoring_engine = ScoringEngine()
        self.strategy_registry = BookingStrategyRegistry()
        self.ranking_engine = RankingEngine()
        self.conflict_resolver = ConflictResolver()
        self.explanation_engine = ExplanationEngine()
        self.audit_engine = AuditEngine()
        self.metrics_engine = MetricsEngine()
        self.health_engine = HealthEngine()
        self.event_publisher = BookingEventPublisher()

        # RecommendationEngine simulation inline
        class MockRecEngine:
            async def compile_recommendations(
                self, primary, alternatives, correlation_id
            ):
                from app.booking.dto.models import BookingRecommendationDTO
                import time

                return BookingRecommendationDTO(
                    recommendation_id="rec_bkg_test",
                    correlation_id=correlation_id,
                    primary_candidate=primary,
                    alternative_candidates=alternatives,
                    generated_at=time.time(),
                    decision_version="1.0.0",
                    ttl_seconds=900,
                )

        self.recommendation_engine = MockRecEngine()

        self.coordinator = BookingCoordinator(
            candidate_builder=self.candidate_builder,
            availability_engine=self.availability_engine,
            confirmation_engine=self.confirmation_engine,
            quota_engine=self.quota_engine,
            boarding_engine=self.boarding_engine,
            constraint_engine=self.constraint_engine,
            risk_engine=self.risk_engine,
            scoring_engine=self.scoring_engine,
            ranking_engine=self.ranking_engine,
            conflict_resolver=self.conflict_resolver,
            explanation_engine=self.explanation_engine,
            recommendation_engine=self.recommendation_engine,
            audit_engine=self.audit_engine,
            metrics_engine=self.metrics_engine,
            event_publisher=self.event_publisher,
        )

        self.gateway = BookingIntelligenceGateway(coordinator=self.coordinator)

    def test_factory_validation(self):
        req = BookingRequestDTO(
            traveler_id="",  # invalid
            journey_id="jrn_01",
            preferences={},
        )
        with self.assertRaises(ValueError):
            BookingDecisionContextFactory.create_context(req, "corr-01")

        req_ok = BookingRequestDTO(
            traveler_id="user_01", journey_id="jrn_01", preferences={}
        )
        context = BookingDecisionContextFactory.create_context(req_ok, "corr-01")
        self.assertEqual(context.correlation_id, "corr-01")
        self.assertEqual(context.request.traveler_id, "user_01")

    def test_quota_engine_resolution(self):
        profile_senior = {"is_senior": True, "is_female": False}
        quota_senior = self.quota_engine.resolve_quotas(profile_senior, None)
        self.assertEqual(quota_senior.quota_code, "SS")
        self.assertIn("SS", quota_senior.eligible_quotas)

        profile_female = {"is_senior": False, "is_female": True}
        quota_female = self.quota_engine.resolve_quotas(profile_female, None)
        self.assertEqual(quota_female.quota_code, "LD")

    def test_boarding_optimization(self):
        # Setup candidate
        from app.booking.dto.models import BookingCandidateDTO

        candidate = BookingCandidateDTO(
            candidate_id="c_01",
            journey_id="j_01",
            segments=[],
            selected_quota="GN",
            boarding_point="JHS",
            class_code="3A",
            estimated_fare=500.0,
        )
        # Shift enabled
        boarding_opt = self.boarding_engine.optimize_boarding(
            candidate, {"enable_boarding_shift": True}
        )
        self.assertTrue(boarding_opt.boarding_point_changed)
        self.assertEqual(boarding_opt.boarding_station, "NDLS")

        # Shift disabled
        boarding_std = self.boarding_engine.optimize_boarding(
            candidate, {"enable_boarding_shift": False}
        )
        self.assertFalse(boarding_std.boarding_point_changed)
        self.assertEqual(boarding_std.boarding_station, "JHS")

    def test_constraints_pruning(self):
        from app.booking.dto.models import BookingCandidateDTO

        candidates = [
            BookingCandidateDTO(
                candidate_id="c_cheap",
                journey_id="j_01",
                segments=[],
                selected_quota="GN",
                boarding_point="NDLS",
                class_code="SL",
                estimated_fare=350.0,
            ),
            BookingCandidateDTO(
                candidate_id="c_expensive",
                journey_id="j_01",
                segments=[],
                selected_quota="GN",
                boarding_point="NDLS",
                class_code="1A",
                estimated_fare=2500.0,
            ),
        ]
        # Restrict max budget to 1000
        pruned = self.constraint_engine.prune_candidates(
            candidates, {"max_budget": 1000.0}
        )
        self.assertEqual(len(pruned), 1)
        self.assertEqual(pruned[0].candidate_id, "c_cheap")

    def test_gateway_and_pipeline(self):
        req = BookingRequestDTO(
            traveler_id="user_123",
            journey_id="journey_999",
            preferences={
                "enable_boarding_shift": True,
                "is_senior": True,
                "max_budget": 3000.0,
            },
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        recommendation = loop.run_until_complete(
            self.gateway.process_booking_query(req, "correlation-9902")
        )
        self.assertIsNotNone(recommendation.primary_candidate)
        self.assertEqual(recommendation.correlation_id, "correlation-9902")
        primary = recommendation.primary_candidate

        # Verify scores and risks are compiled
        self.assertTrue(0.0 <= primary.score.overall_score <= 100.0)
        self.assertIn(
            primary.risk.overall_risk_level, ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        )
        self.assertTrue(len(primary.explanation.get("reason_codes", [])) > 0)
        loop.close()


if __name__ == "__main__":
    unittest.main()
