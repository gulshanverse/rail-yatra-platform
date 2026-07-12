from typing import Protocol, runtime_checkable

@runtime_checkable
class ProviderFeatureFlags(Protocol):
    """
    Abstract feature flag interface for managing LLM providers.
    Supports canary rollouts and emergency kill switches.
    """
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Checks if a provider is globally enabled."""
        ...

    def is_canary_active(self, provider_name: str, model_name: str) -> bool:
        """Determines if a model is undergoing canary rollout constraints."""
        ...

    def check_emergency_disable(self, provider_name: str) -> bool:
        """Checks if emergency shutdown override flag is set for the provider."""
        ...
