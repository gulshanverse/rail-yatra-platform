from abc import ABC, abstractmethod
from app.llm.interfaces import (
    LLMProvider,
    ProviderMetadata,
    HealthMetadata,
    ChatRequest,
    ChatResponse,
)


class BaseProvider(LLMProvider, ABC):
    """
    Abstract Base Class for LLM providers.
    All concrete provider integrations must inherit from this class.
    """

    def __init__(self, name: str) -> None:
        self._name = name.strip().lower()

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def get_metadata(self) -> ProviderMetadata:
        """Returns static metadata describing the models and features of this provider."""
        ...

    @abstractmethod
    async def check_health(self) -> HealthMetadata:
        """Checks API configurations and remote service health."""
        ...

    @abstractmethod
    async def generate(self, request: ChatRequest) -> ChatResponse:
        """Invokes chat generation logic."""
        ...
