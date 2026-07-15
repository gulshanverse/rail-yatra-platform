# app/integration/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Type, Optional
from pydantic import BaseModel
from app.integration.models import ProviderMetadata, CorrelationContext


class NormalizedResponse(BaseModel):
    success: bool
    provider_id: str
    latency_ms: float
    data: Dict[str, Any]
    error_message: Optional[str] = None


class IIntegrationGateway(ABC):
    @abstractmethod
    async def execute(
        self,
        capability: str,
        payload: Dict[str, Any],
        context: Optional[CorrelationContext] = None,
    ) -> NormalizedResponse:
        """Executes the integration query by validating, routing, and translating responses."""
        pass


class IProviderRegistry(ABC):
    @abstractmethod
    def get_providers_for_capability(self, capability: str) -> List[ProviderMetadata]:
        """Returns registered metadata configs matching capability name, prioritized."""
        pass

    @abstractmethod
    def update_provider_status(self, provider_id: str, status: str) -> None:
        """Updates availability status of target provider dynamically."""
        pass

    @abstractmethod
    def list_all_providers(self) -> List[ProviderMetadata]:
        """Lists all registered providers."""
        pass


class IProviderRouter(ABC):
    @abstractmethod
    def resolve_provider(
        self, capability: str, policy: str = "business_priority"
    ) -> ProviderMetadata:
        """Resolves target provider using configured routing profile and registry availability."""
        pass


class IProviderAdapter(ABC):
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Returns unique identifier of adapter."""
        pass

    @abstractmethod
    async def execute_query(
        self, capability: str, params: Dict[str, Any], response_model: Type[BaseModel]
    ) -> BaseModel:
        """Translates schema structures and routes HTTP payloads to external API endpoints."""
        pass


class IAuthenticationManager(ABC):
    @abstractmethod
    async def get_auth_headers(self, provider_id: str) -> Dict[str, str]:
        """Generates dynamic authorization context values."""
        pass

    @abstractmethod
    def configure_ssl_context(self, provider_id: str) -> Any:
        """Generates client SSL context configuration parameters."""
        pass


class ICredentialVault(ABC):
    @abstractmethod
    async def get_secret(self, key: str) -> str:
        """Decrypted secret value extraction hook."""
        pass


class IRateLimiter(ABC):
    @abstractmethod
    async def check_rate_limit(self, provider_id: str, capability: str) -> bool:
        """Asserts client rate limit tokens are available."""
        pass


class IIdempotencyEngine(ABC):
    @abstractmethod
    async def acquire_lock(
        self, key: str, request_id: str, ttl_seconds: int = 300
    ) -> bool:
        """Claims unique lock inside dynamic cache partition."""
        pass

    @abstractmethod
    async def save_response(self, key: str, response: Dict[str, Any]) -> None:
        """Caches request reply payload against the key."""
        pass

    @abstractmethod
    async def get_response(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves cached reply payload if present."""
        pass


class IBulkOperationAdapter(ABC):
    @abstractmethod
    async def execute_bulk(
        self, capability: str, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Placeholder extension interface logic for bulk requests."""
        pass


class ICapabilityNegotiator(ABC):
    @abstractmethod
    def negotiate_capability(
        self, provider_id: str, capability: str, requested_version: str
    ) -> Tuple[bool, str]:
        """Performs pre-flight handshake checking specs."""
        pass
