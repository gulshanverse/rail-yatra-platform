import unittest
import asyncio
from typing import Dict, Any, AsyncIterator
from app.orchestrator.state import AIState
from app.orchestrator.registry import agent_registry
from app.orchestrator.interfaces import IAgent
from app.orchestrator.nodes import (
    ClassifierNode,
    RouterNode,
    AgentNode,
    MemoryNode,
    ResponseNode,
    ErrorNode
)

class MockAgent(IAgent):
    name = "MockAgent"
    system_prompt = "Mock system prompt"
    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        return f"Response for: {user_message}"
    async def run_stream(self, user_message: str, context: Dict[str, Any] = None) -> AsyncIterator[str]:
        raise NotImplementedError()

class TestNodes(unittest.TestCase):
    def setUp(self):
        self.mock_agent = MockAgent()
        agent_registry.register("mock_agent_key", self.mock_agent)
        
        self.state: AIState = {
            "request_id": "req-t",
            "trace_id": "tr-t",
            "conversation_id": "conv-t",
            "user_id": "user-t",
            "message": "Verify this request",
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
            "timestamps": {"workflow_start_time": 0.0}
        }
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def tearDown(self):
        self.loop.close()

    def test_classifier_node(self):
        async def run_test():
            node = ClassifierNode()
            state = await node(self.state)
            self.assertIsNotNone(state["intent"])
            self.assertIn("ClassifierNode", state["execution_path"])
        self.loop.run_until_complete(run_test())

    def test_router_node(self):
        async def run_test():
            node = RouterNode()
            self.state["intent"] = "plan_travel"
            state = await node(self.state)
            self.assertEqual(state["selected_agent"], "travel_decision")
            self.assertIn("RouterNode", state["execution_path"])
        self.loop.run_until_complete(run_test())

    def test_agent_node(self):
        async def run_test():
            node = AgentNode()
            self.state["selected_agent"] = "mock_agent_key"
            state = await node(self.state)
            self.assertEqual(state["response"], "Response for: Verify this request")
            self.assertIn("AgentNode", state["execution_path"])
        self.loop.run_until_complete(run_test())

    def test_memory_node(self):
        async def run_test():
            node = MemoryNode()
            state = await node(self.state)
            self.assertIn("MemoryNode", state["execution_path"])
        self.loop.run_until_complete(run_test())

    def test_response_node(self):
        async def run_test():
            node = ResponseNode()
            state = await node(self.state)
            self.assertIn("ResponseNode", state["execution_path"])
            self.assertIn("trace_id", state["metadata"])
        self.loop.run_until_complete(run_test())

    def test_error_node(self):
        async def run_test():
            node = ErrorNode()
            state = await node(self.state)
            self.assertTrue(len(state["response"]) > 0)
            self.assertIn("ErrorNode", state["execution_path"])
        self.loop.run_until_complete(run_test())

if __name__ == "__main__":
    unittest.main()
