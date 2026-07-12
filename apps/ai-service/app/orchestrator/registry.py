import logging
from typing import Dict, Optional
from app.orchestrator.interfaces import IAgent, IRegistry

logger = logging.getLogger("ai-service.orchestrator.registry")

class AgentRegistry(IRegistry):
    """
    Registry pattern mapping agent identifiers to concrete agent instances.
    Provides dependency lookup and supports registration on startup.
    """
    _instance: Optional["AgentRegistry"] = None

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}
        return cls._instance

    def register(self, key: str, agent: IAgent) -> None:
        if not isinstance(agent, IAgent):
            raise TypeError(f"Object registered under '{key}' must conform to IAgent protocol.")
        self._registry[key] = agent
        logger.info(f"Successfully registered agent: key='{key}' class='{agent.__class__.__name__}'")

    def get(self, key: str) -> IAgent:
        if key not in self._registry:
            raise KeyError(f"Specialist agent '{key}' is not registered in the AgentRegistry.")
        return self._registry[key]

# Export singleton registry instance
agent_registry = AgentRegistry()

# Register core concrete agents dynamically on module load
try:
    from app.agents.travel_decision import TravelDecisionAgent
    from app.agents.prediction import TicketPredictionAgent
    from app.agents.pnr import PNRAgent
    from app.agents.knowledge import KnowledgeAgent
    from app.agents.conversation import ConversationAgent

    agent_registry.register("travel_decision", TravelDecisionAgent())
    agent_registry.register("prediction", TicketPredictionAgent())
    agent_registry.register("pnr", PNRAgent())
    agent_registry.register("knowledge", KnowledgeAgent())
    agent_registry.register("conversation", ConversationAgent())
except Exception as e:
    logger.error(f"Error registering default concrete agents: {e}", exc_info=True)
