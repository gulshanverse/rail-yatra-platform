import unittest
import asyncio
from app.orchestrator.workflow import workflow_executor
from app.orchestrator.types import AIResponse
from app.orchestrator.registry import agent_registry
from app.orchestrator.interfaces import IAgent
from typing import Dict, Any, AsyncIterator


class WorkflowMockAgent(IAgent):
    name = "WorkflowMockAgent"
    system_prompt = "Chitchat prompt"

    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        return f"Response to: {user_message}"

    async def run_stream(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError()


class TestWorkflow(unittest.TestCase):
    def setUp(self):
        # Register a mock conversation agent
        self.agent = WorkflowMockAgent()
        agent_registry.register("conversation", self.agent)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_workflow_execution(self):
        async def run_test():
            response = await workflow_executor.execute(
                message="Test query", user_id="user-w", conversation_id="conv-w"
            )
            self.assertIsInstance(response, AIResponse)
            self.assertEqual(response.response, "Response to: Test query")
            self.assertEqual(response.intent, "conversation")
            self.assertEqual(response.agent, "conversation")
            self.assertTrue(response.latency_ms > 0.0)
            self.assertEqual(len(response.errors), 0)

        self.loop.run_until_complete(run_test())

    def test_workflow_execution_crash(self):
        async def run_test():
            from app.orchestrator.workflow import get_compiled_graph

            class BrokenGraph:
                async def ainvoke(self, state, config=None):
                    raise RuntimeError("Pregel runner crashed")

            original_get_graph = get_compiled_graph

            import app.orchestrator.workflow

            app.orchestrator.workflow.get_compiled_graph = lambda: BrokenGraph()  # type: ignore

            try:
                response = await workflow_executor.execute(
                    message="Trigger crash",
                    user_id="user-crash",
                    conversation_id="conv-crash",
                )
                self.assertIsInstance(response, AIResponse)
                self.assertEqual(response.agent, "unknown")
                self.assertTrue("crashed" in response.errors[0])
                self.assertTrue(len(response.response) > 0)
            finally:
                app.orchestrator.workflow.get_compiled_graph = original_get_graph

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
