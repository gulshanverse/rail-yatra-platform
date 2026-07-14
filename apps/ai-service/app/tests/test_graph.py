import unittest
import asyncio
from app.orchestrator.graph import get_compiled_graph
from app.orchestrator.state import AIState
from app.orchestrator.registry import agent_registry
from app.orchestrator.interfaces import IAgent
from typing import Dict, Any, AsyncIterator


class DummyConversationAgent(IAgent):
    name = "DummyConversationAgent"
    system_prompt = "Chitchat"

    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        return "mock chat reply"

    async def run_stream(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError()


class TestGraph(unittest.TestCase):
    def setUp(self):
        # Register a conversation agent to handle default routing path during graph run
        self.agent = DummyConversationAgent()
        agent_registry.register("conversation", self.agent)

        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_graph_compile(self):
        graph = get_compiled_graph()
        self.assertIsNotNone(graph)

    def test_graph_execution_path(self):
        async def run_test():
            graph = get_compiled_graph()
            state: AIState = {
                "request_id": "req-g",
                "trace_id": "tr-g",
                "conversation_id": "conv-g",
                "user_id": "user-g",
                "message": "hello",
                "intent": None,
                "selected_agent": None,
                "execution_path": [],
                "current_node": None,
                "tool_calls": [],
                "context": {},
                "memory": [],
                "metadata": {},
                "response": "",
                "latency_ms": 0.0,
                "errors": [],
                "timestamps": {"workflow_start_time": 0.0},
            }
            final_state = await graph.ainvoke(state)
            self.assertEqual(final_state["response"], "mock chat reply")
            self.assertIn("ClassifierNode", final_state["execution_path"])
            self.assertIn("RouterNode", final_state["execution_path"])
            self.assertIn("conversation", final_state["execution_path"])
            self.assertIn("MemoryNode", final_state["execution_path"])
            self.assertIn("ResponseNode", final_state["execution_path"])

        self.loop.run_until_complete(run_test())


if __name__ == "__main__":
    unittest.main()
