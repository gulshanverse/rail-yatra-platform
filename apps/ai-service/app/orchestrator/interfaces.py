from typing import Dict, Any, AsyncIterator, Protocol, runtime_checkable, Optional
from app.orchestrator.types import AIResponse
from app.orchestrator.state import AIState


@runtime_checkable
class IAgent(Protocol):
    """
    Protocol definition for specialized agents.
    Every specialist agent must comply with this interface.
    """

    name: str
    system_prompt: str

    async def run(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Runs the agent synchronously and returns the complete text response."""
        ...

    def run_stream(
        self, user_message: str, context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Runs the agent and streams the response token-by-token."""
        ...


class IRouter(Protocol):
    """
    Protocol definition for the Routing component.
    """

    async def route(self, intent: str) -> str:
        """
        Determines which specialist agent key should execute the user message.
        """
        ...


class IRegistry(Protocol):
    """
    Protocol definition for the Agent Registry.
    """

    def register(self, key: str, agent: IAgent) -> None:
        """Registers a specialist agent instance under a string key."""
        ...

    def get(self, key: str) -> IAgent:
        """Retrieves a registered specialist agent by its string key."""
        ...


class IWorkflow(Protocol):
    """
    Protocol definition for the end-to-end execution workflow.
    """

    async def execute(
        self,
        message: str,
        user_id: str,
        conversation_id: str,
        context: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
    ) -> AIResponse:
        """
        Runs the orchestrated graph pipeline and returns a structured response.
        """
        ...


class IGraphNode(Protocol):
    """
    Protocol definition for reusable LangGraph nodes.
    """

    async def __call__(self, state: AIState) -> AIState:
        """
        Executes node logic, mutating state and returning the updated state.
        """
        ...
