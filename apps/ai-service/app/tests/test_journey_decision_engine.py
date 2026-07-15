# app/tests/test_journey_decision_engine.py
import unittest
import asyncio
from datetime import datetime, timedelta
from app.journey.dto.models import JourneyQueryDTO
from app.journey.gateway.coordinator import JourneyIntelligenceGateway
from app.journey.candidate.builder import JourneyCandidateBuilder
from app.journey.constraints.engine import ConstraintEngine
from app.journey.route.analyzer import RouteAnalyzer
from app.journey.transfer.analyzer import TransferAnalyzer
from app.journey.risk.engine import RiskEngine
from app.journey.scoring.engine import ScoringEngine
from app.journey.ranking.engine import RankingEngine
from app.journey.explanation.engine import ExplanationEngine
from app.journey.audit.logger import AuditEngine
from app.journey.metrics.collector import MetricsEngine
from app.journey.events.publisher import JourneyEventPublisher


class TestJourneyDecisionEngine(unittest.TestCase):
    def setUp(self):
        self.candidate_builder = JourneyCandidateBuilder()
        self.constraint_engine = ConstraintEngine()
        self.route_analyzer = RouteAnalyzer()
        self.transfer_analyzer = TransferAnalyzer()
        self.risk_engine = RiskEngine()
        self.scoring_engine = ScoringEngine()
        self.ranking_engine = RankingEngine()
        self.explanation_engine = ExplanationEngine()
        self.audit_engine = AuditEngine()
        self.metrics_engine = MetricsEngine()
        self.event_publisher = JourneyEventPublisher()

        self.gateway = JourneyIntelligenceGateway(
            candidate_builder=self.candidate_builder,
            constraint_engine=self.constraint_engine,
            route_analyzer=self.route_analyzer,
            transfer_analyzer=self.transfer_analyzer,
            risk_engine=self.risk_engine,
            scoring_engine=self.scoring_engine,
            ranking_engine=self.ranking_engine,
            explanation_engine=self.explanation_engine,
            audit_engine=self.audit_engine,
            metrics_engine=self.metrics_engine,
            event_publisher=self.event_publisher,
        )

    def test_invariants_origin_destination(self):
        query = JourneyQueryDTO(
            origin="NDLS",
            destination="NDLS",  # invariant violation
            earliest_departure=datetime.now(),
            latest_arrival=datetime.now() + timedelta(hours=10),
            traveler_profile={},
            preference_weights={},
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with self.assertRaises(ValueError):
            loop.run_until_complete(self.gateway.process_journey_query(query, "tr-01"))
        loop.close()

    def test_candidate_generation(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        candidates = loop.run_until_complete(
            self.candidate_builder.build_candidates(
                "NDLS", "BPL", datetime.now(), datetime.now() + timedelta(hours=12)
            )
        )
        self.assertTrue(len(candidates) >= 1)
        for c in candidates:
            self.assertNotEqual(c.journey_id, "")
            self.assertTrue(len(c.segments) >= 1)
        loop.close()

    def test_constraint_filtering(self):
        # Generate candidates NDLS -> BPL
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        candidates = loop.run_until_complete(
            self.candidate_builder.build_candidates(
                "NDLS", "BPL", datetime.now(), datetime.now() + timedelta(hours=12)
            )
        )

        # Apply tight budget constraint (e.g. max 400 INR)
        # Connecting segments nominal cost is 1200, direct is 600
        pruned_budget = self.constraint_engine.evaluate_constraints(
            candidates, {"max_budget": 400.0}
        )
        self.assertEqual(len(pruned_budget), 0)

        # Apply high budget
        pruned_ok = self.constraint_engine.evaluate_constraints(
            candidates, {"max_budget": 5000.0}
        )
        self.assertTrue(len(pruned_ok) > 0)
        loop.close()

    def test_scoring_and_ranking(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        query = JourneyQueryDTO(
            origin="NDLS",
            destination="BPL",
            earliest_departure=datetime.now(),
            latest_arrival=datetime.now() + timedelta(hours=15),
            traveler_profile={"is_senior": True, "max_budget": 2000.0},
            preference_weights={
                "reliability": 0.40,
                "comfort": 0.20,
                "cost": 0.20,
                "duration": 0.20,
            },
        )

        recommendation = loop.run_until_complete(
            self.gateway.process_journey_query(query, "tr-102")
        )
        self.assertIsNotNone(recommendation.primary_candidate)
        self.assertNotEqual(recommendation.recommendation_id, "")
        self.assertEqual(recommendation.correlation_id, "tr-102")

        # Verify scores are bounded [0, 100]
        primary = recommendation.primary_candidate
        self.assertTrue(0.0 <= primary.score.overall_score <= 100.0)
        self.assertTrue(0.0 <= primary.score.reliability_subscore <= 100.0)

        # Verify risk output is present
        self.assertIn(
            primary.risk.overall_risk_level, ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        )

        # Verify explanation reason codes exist
        self.assertTrue(len(primary.explanation.reason_codes) > 0)
        loop.close()


if __name__ == "__main__":
    unittest.main()
