import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("ai-service.orchestrator.capabilities")


class CapabilityMetadata(BaseModel):
    """
    Metadata describing an AI specialist capability.
    Serves as the single source of truth for downstream planning and routing.
    """

    identity: str = Field(description="Unique capability identifier.")
    display_name: str = Field(description="Human-readable name.")
    description: str = Field(
        description="Detailed capability responsibilities description."
    )
    category: str = Field(
        default="general", description="Capability category classification."
    )
    supported_intents: List[str] = Field(
        default_factory=list, description="Intent families mapped."
    )
    priority: int = Field(
        default=100, description="Routing execution priority hierarchy."
    )
    confidence_threshold: float = Field(
        default=0.5, description="Minimum confidence threshold."
    )
    cost_classification: str = Field(
        default="low", description="Resource or token cost tier."
    )
    permissions: List[str] = Field(
        default_factory=list, description="Authorization permissions required."
    )
    availability: bool = Field(
        default=True, description="Active runtime availability status."
    )
    lifecycle_status: str = Field(
        default="active", description="Status (e.g. active, deprecated, beta)."
    )
    version: str = Field(default="1.0.0", description="Semantic capability version.")
    compatibility: List[str] = Field(
        default_factory=list, description="Compatible state versions."
    )
    observability_metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Custom tracing tags."
    )


class AICapabilityRegistry:
    """
    Registry pattern managing metadata for all operational specialist capabilities.
    """

    def __init__(self) -> None:
        self._capabilities: Dict[str, CapabilityMetadata] = {}

    def register_capability(self, capability: CapabilityMetadata) -> None:
        """Registers capability metadata."""
        self._capabilities[capability.identity] = capability
        logger.info(
            f"Registered capability metadata: {capability.identity} (v{capability.version})"
        )

    def get_capability(self, identity: str) -> Optional[CapabilityMetadata]:
        """Retrieves metadata by capability identifier."""
        return self._capabilities.get(identity)

    def list_capabilities(self) -> List[CapabilityMetadata]:
        """Lists all registered capability metadata records."""
        return list(self._capabilities.values())


# Global singleton Capability Registry
capability_registry = AICapabilityRegistry()
