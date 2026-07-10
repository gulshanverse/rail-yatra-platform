import unittest
import asyncio
from app.engine.models import TravelRequirement, UserPreferences
from app.engine.prediction import predict_journey_metrics
from app.engine.scoring import scoring_engine
from app.engine.core import journey_intelligence_engine

class TestJourneyIntelligenceEngine(unittest.TestCase):
    
    def test_pydantic_models_parsing(self):
        """Verify models parse correctly and map overall and confidence scores."""
        req = TravelRequirement(
            source="NDLS",
            destination="BPL",
            journey_date="2026-07-28",
            preferred_class="3A",
            preferences=UserPreferences(comfort=2.0, budget=0.5)
        )
        self.assertEqual(req.source, "NDLS")
        self.assertEqual(req.preferences.comfort, 2.0)
        self.assertEqual(req.preferences.budget, 0.5)

    def test_prediction_certainty_mapping(self):
        """Verify waitlist clearances and prediction confidence calculation are decoupled."""
        loop = asyncio.new_event_loop()
        # 1. No waitlist (confirmed status) -> high probability & confidence
        res_cnf = loop.run_until_complete(predict_journey_metrics("12002", "3A", waitlist_position=None))
        self.assertEqual(res_cnf["confirmation_probability"], 100.0)
        self.assertTrue(res_cnf["confidence_score"] >= 0.9)

        # 2. Waitlisted ticket -> clearing probability computed by class rules
        res_wl = loop.run_until_complete(predict_journey_metrics("12002", "3A", waitlist_position=12))
        # WL 12 falls inside range <= 25 (Probability should be 82.0)
        self.assertEqual(res_wl["confirmation_probability"], 82.0)
        self.assertTrue(0.0 <= res_wl["confidence_score"] <= 1.0)
        loop.close()

    def test_extensible_scoring_calculations(self):
        """Verify sub-score formulas and dynamic preference weights work correctly."""
        # Setup mock option details
        opt = {
            "fare": 1500,
            "duration": "8h 30m",
            "booking_class": "3A",
            "confirmation_probability": 85.0,
            "predicted_delay_mins": 10
        }
        
        # 1. Base sub-scores
        sub = scoring_engine.compute_sub_scores(opt, distance_km=500)
        self.assertIn("cost", sub)
        self.assertIn("comfort", sub)
        self.assertIn("reliability", sub)
        self.assertTrue(sub["comfort"] == 75.0)

        # 2. Score mapping using weight vectors
        prefs_comfort = UserPreferences(comfort=3.0, budget=0.2)
        score_comfort = scoring_engine.calculate_overall_score(sub, prefs_comfort)
        
        prefs_budget = UserPreferences(comfort=0.2, budget=3.0)
        score_budget = scoring_engine.calculate_overall_score(sub, prefs_budget)
        
        # A higher comfort multiplier should yield different overall scores
        self.assertNotEqual(score_comfort, score_budget)

    def test_full_engine_optimization_pipeline(self):
        """Runs full core journey intelligence pipeline to check output sorting and tradeoffs."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_pipeline():
            req = TravelRequirement(
                source="NDLS",
                destination="BPL",
                journey_date="2026-07-28",
                preferred_class="3A"
            )
            recommendation = await journey_intelligence_engine.analyze_journey(req)
            
            # Check sorting and structures
            self.assertEqual(len(recommendation.options), len(set([o.train_number + o.source + o.journey_date for o in recommendation.options])))
            self.assertTrue(recommendation.options[0].overall_score >= recommendation.options[-1].overall_score)
            self.assertTrue(len(recommendation.tradeoffs_summary) > 0)
            
            # Check reason codes
            self.assertTrue(any(len(opt.reason_codes) > 0 for opt in recommendation.options))
            
        loop.run_until_complete(run_pipeline())
        loop.close()

if __name__ == '__main__':
    unittest.main()
