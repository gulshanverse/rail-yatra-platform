import unittest
import asyncio
from app.providers.llm import get_chat_model, MockChatModel
from app.memory.short_term import short_term_memory
from app.orchestrator.classifier import intent_classifier
from app.orchestrator.graph import compiled_graph


class TestAIServiceCore(unittest.TestCase):
    def test_llm_provider_fallback(self):
        """Verify that provider abstraction correctly falls back to MockChatModel."""
        model = get_chat_model("openai", "gpt-4o-mini")
        self.assertIsInstance(model, MockChatModel)
        self.assertEqual(model.provider_name, "mock")

    def test_short_term_memory(self):
        """Verify that Redis/local short term memory correctly caches context and history."""
        session_id = "test-session-123"
        context = {"current_page": "/dashboard", "selected_train": "12002"}

        async def run_test():
            # Test session context saving/loading
            await short_term_memory.save_session_context(session_id, context)
            loaded_context = await short_term_memory.get_session_context(session_id)
            self.assertEqual(loaded_context["current_page"], "/dashboard")
            self.assertEqual(loaded_context["selected_train"], "12002")

            # Test sliding window history
            await short_term_memory.add_message(session_id, "user", "Hello AI")
            await short_term_memory.add_message(
                session_id, "assistant", "Hello Passenger"
            )
            history = await short_term_memory.get_history(session_id)

            self.assertEqual(len(history), 2)
            self.assertEqual(history[0]["role"], "user")
            self.assertEqual(history[0]["content"], "Hello AI")
            self.assertEqual(history[1]["role"], "assistant")
            self.assertEqual(history[1]["content"], "Hello Passenger")

        asyncio.run(run_test())

    def test_intent_classification(self):
        """Verify that the intent classifier node returns appropriate intent labels."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_classification():
            # Query mapped to plan_travel
            res_travel = await intent_classifier.classify(
                "I want to travel from NDLS to BPL next Monday"
            )
            self.assertEqual(res_travel["intent"], "plan_travel")

            # Query mapped to check_pnr
            res_pnr = await intent_classifier.classify(
                "Check status for PNR 4210987654"
            )
            self.assertEqual(res_pnr["intent"], "check_pnr")

            # Query mapped to journey_intelligence
            res_intel = await intent_classifier.classify(
                "what is the confirmation probability of waitlist WL 14?"
            )
            self.assertEqual(res_intel["intent"], "journey_intelligence")

            # Query mapped to general conversation
            res_conv = await intent_classifier.classify("hello there, who are you?")
            self.assertEqual(res_conv["intent"], "conversation")

        loop.run_until_complete(run_classification())
        loop.close()

    def test_langgraph_execution(self):
        """Verify that invoking the compiled LangGraph correctly executes routing and returns response."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def run_graph():
            inputs = {
                "user_message": "Hello, search trains from HWH to CSMT",
                "context": {"user_id": "test-user"},
                "history": [],
            }
            state = await compiled_graph.ainvoke(inputs)
            self.assertIn("response", state)
            self.assertIn("intent", state)
            self.assertEqual(state["intent"], "plan_travel")
            self.assertTrue(len(state["response"]) > 0)

        loop.run_until_complete(run_graph())
        loop.close()


if __name__ == "__main__":
    unittest.main()
