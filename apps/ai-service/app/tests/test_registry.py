import unittest
from app.orchestrator.registry import AgentRegistry
from app.orchestrator.interfaces import IAgent
from typing import Dict, Any, AsyncIterator


class DummyAgent(IAgent):
    name = "DummyAgent"
    system_prompt = "Hello"

    async def run(self, user_message: str, context: Dict[str, Any] = None) -> str:
        return "dummy response"

    async def run_stream(
        self, user_message: str, context: Dict[str, Any] = None
    ) -> AsyncIterator[str]:
        raise NotImplementedError()


class TestAgentRegistry(unittest.TestCase):
    def test_registry_operations(self):
        registry = AgentRegistry()
        dummy = DummyAgent()

        # Test registration
        registry.register("dummy_key", dummy)
        self.assertEqual(registry.get("dummy_key"), dummy)

        # Test lookup errors
        with self.assertRaises(KeyError):
            registry.get("non_existent_key")

        # Test type validation errors
        with self.assertRaises(TypeError):
            registry.register("invalid_agent", "not_an_agent_instance")  # type: ignore


if __name__ == "__main__":
    unittest.main()
