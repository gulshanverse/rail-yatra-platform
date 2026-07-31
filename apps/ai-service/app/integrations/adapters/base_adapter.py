"""
Base Provider Adapter Abstract Class for Phase 9 Enterprise Integrations Platform.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.integrations.models import ProviderConfiguration


class BaseAdapter(ABC):
    def __init__(self, config: ProviderConfiguration) -> None:
        self.config = config
        self.is_initialized: bool = False
        self.is_authenticated: bool = False

    @abstractmethod
    def initialize(self) -> None:
        """Initializes client connections or resources."""
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Authenticates with the third-party provider."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Performs a health check ping to the provider."""
        pass

    @abstractmethod
    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes an action request against the provider."""
        pass

    @abstractmethod
    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes provider-specific responses into standardized domain schemas."""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        """Cleans up adapter resources."""
        pass
