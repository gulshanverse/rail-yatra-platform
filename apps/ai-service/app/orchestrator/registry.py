import logging
import threading
from typing import Optional, Dict
from app.orchestrator.interfaces import IAgent, IRegistry

logger = logging.getLogger("ai-service.orchestrator.registry")


class AgentRegistry(IRegistry):
    """
    Registry pattern mapping agent identifiers to concrete agent instances.
    Provides dependency lookup and supports registration on startup.
    Thread-safe implementation for instantiation and register/get lookups.
    """

    _instance: Optional["AgentRegistry"] = None
    _lock: threading.Lock = threading.Lock()
    _registry: Dict[str, IAgent]
    _registry_lock: threading.Lock
    _active_states: Dict[str, bool]
    _health_states: Dict[str, str]
    _versions: Dict[str, str]

    def __new__(cls) -> "AgentRegistry":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._registry = {}
                    cls._instance._registry_lock = threading.Lock()
                    cls._instance._active_states = {}
                    cls._instance._health_states = {}
                    cls._instance._versions = {}
        return cls._instance

    def register(self, key: str, agent: IAgent) -> None:
        if not isinstance(agent, IAgent):
            raise TypeError(
                f"Object registered under '{key}' must conform to IAgent protocol."
            )
        with self._registry_lock:
            self._registry[key] = agent
            self._active_states[key] = True
            self._health_states[key] = "healthy"
            self._versions[key] = "1.0.0"
        logger.info(
            f"Successfully registered agent: key='{key}' class='{agent.__class__.__name__}'"
        )

    def register_versioned(
        self, key: str, agent: IAgent, version: str = "1.0.0"
    ) -> None:
        """Registers a versioned specialist agent to the platform registry."""
        self.register(key, agent)
        with self._registry_lock:
            self._versions[key] = version

    def activate(self, key: str) -> None:
        """Enables a specialist agent capability."""
        with self._registry_lock:
            if key in self._registry:
                self._active_states[key] = True
                logger.info(f"Activated agent: key='{key}'")

    def deactivate(self, key: str) -> None:
        """Disables a specialist agent capability."""
        with self._registry_lock:
            if key in self._registry:
                self._active_states[key] = False
                logger.info(f"Deactivated agent: key='{key}'")

    def set_health(self, key: str, status: str) -> None:
        """Updates the health status flag for a registered agent."""
        with self._registry_lock:
            if key in self._registry:
                self._health_states[key] = status
                logger.info(f"Updated agent health: key='{key}' status='{status}'")

    def get_health(self, key: str) -> str:
        """Retrieves active health status for an agent."""
        with self._registry_lock:
            return self._health_states.get(key, "unknown")

    def get_version(self, key: str) -> str:
        """Retrieves semantic version tag for a registered agent."""
        with self._registry_lock:
            return self._versions.get(key, "1.0.0")

    def is_active(self, key: str) -> bool:
        """Evaluates activation status of a registered agent."""
        with self._registry_lock:
            return self._active_states.get(key, True)

    def get(self, key: str) -> IAgent:
        with self._registry_lock:
            if key not in self._registry:
                raise KeyError(
                    f"Specialist agent '{key}' is not registered in the AgentRegistry."
                )
            if not self._active_states.get(key, True):
                raise RuntimeError(
                    f"Specialist agent '{key}' is registered but currently deactivated."
                )
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
