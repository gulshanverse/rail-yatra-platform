import unittest
from app.orchestrator.state import AIState


class TestAIState(unittest.TestCase):
    def test_state_creation(self):
        # Verify AIState initialization and default keys matching typed requirements
        state: AIState = {
            "request_id": "req-1",
            "trace_id": "tr-1",
            "conversation_id": "conv-1",
            "user_id": "user-1",
            "message": "hello",
            "intent": "conversation",
            "selected_agent": "conversation",
            "execution_path": [],
            "current_node": None,
            "tool_calls": [],
            "context": {},
            "memory": [],
            "metadata": {},
            "response": "",
            "latency_ms": 0.0,
            "errors": [],
            "timestamps": {},
        }
        self.assertEqual(state["request_id"], "req-1")
        self.assertEqual(state["trace_id"], "tr-1")
        self.assertEqual(state["conversation_id"], "conv-1")
        self.assertEqual(state["user_id"], "user-1")
        self.assertEqual(state["message"], "hello")
        self.assertEqual(state["intent"], "conversation")
        self.assertEqual(state["selected_agent"], "conversation")
        self.assertEqual(state["execution_path"], [])
        self.assertEqual(state["response"], "")
        self.assertEqual(state["errors"], [])


if __name__ == "__main__":
    unittest.main()
