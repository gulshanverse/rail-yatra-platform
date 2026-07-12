import unittest
import asyncio
from app.orchestrator.router import router

class TestRouter(unittest.TestCase):
    def test_routing_decisions(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_routing_tests():
            # Test Travel planning mapping
            self.assertEqual(await router.route("plan_travel"), "travel_decision")
            
            # Test Prediction mapping
            self.assertEqual(await router.route("journey_intelligence"), "prediction")
            self.assertEqual(await router.route("prediction"), "prediction")
            
            # Test PNR mapping
            self.assertEqual(await router.route("check_pnr"), "pnr")
            self.assertEqual(await router.route("pnr"), "pnr")
            
            # Test Knowledge mapping
            self.assertEqual(await router.route("knowledge"), "knowledge")
            
            # Test Conversational fallback mapping
            self.assertEqual(await router.route("conversation"), "conversation")
            self.assertEqual(await router.route("random_intent"), "conversation")
            self.assertEqual(await router.route(""), "conversation")
            
        loop.run_until_complete(run_routing_tests())
        loop.close()

if __name__ == "__main__":
    unittest.main()
