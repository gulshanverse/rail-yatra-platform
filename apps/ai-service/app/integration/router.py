# app/integration/router.py
import logging
from app.integration.interfaces import IProviderRouter, IProviderRegistry
from app.integration.models import ProviderMetadata
from app.integration.exceptions import ProviderNetworkError

logger = logging.getLogger("ai-service.integration.router")


class ProviderRouter(IProviderRouter):
    def __init__(self, registry: IProviderRegistry):
        self.registry = registry
        self._manual_overrides = {}  # capability -> provider_id

    def set_manual_override(self, capability: str, provider_id: str) -> None:
        self._manual_overrides[capability] = provider_id

    def clear_manual_override(self, capability: str) -> None:
        self._manual_overrides.pop(capability, None)

    def resolve_provider(
        self, capability: str, policy: str = "business_priority"
    ) -> ProviderMetadata:
        """
        Dynamically selects the best provider from the registry based on routing policy profiles.
        """
        # 1. Check for manual overrides first
        if capability in self._manual_overrides:
            override_id = self._manual_overrides[capability]
            for p in self.registry.list_all_providers():
                if p.provider_id == override_id and p.status != "offline":
                    logger.info(
                        f"Manual Override applied for {capability}: {override_id}"
                    )
                    return p

        # 2. Lookup matching active providers
        candidates = self.registry.get_providers_for_capability(capability)
        if not candidates:
            raise ProviderNetworkError(
                f"No active provider candidates found for capability: {capability}"
            )

        # 3. Apply Routing Policy Profiles
        policy_lower = policy.lower()

        if policy_lower == "lowest_latency":
            # Sort by expected latency (ascending)
            candidates.sort(key=lambda p: p.expected_latency_ms)
        elif policy_lower == "lowest_cost":
            # Sort by cost per query (ascending)
            candidates.sort(key=lambda p: p.cost_per_query_usd)
        elif policy_lower == "highest_availability":
            # Sort by SLA availability (descending)
            candidates.sort(key=lambda p: p.sla_availability, reverse=True)
        elif policy_lower == "highest_accuracy":
            # Accuracy favors direct/official links. In our priority model: lower rank priority is more authoritative
            candidates.sort(key=lambda p: p.priority)
        elif policy_lower == "maintenance_mode":
            # Divert GDS traffic to static/local databases where possible
            static_candidates = [
                c
                for c in candidates
                if "static" in c.provider_id or "local" in c.provider_id
            ]
            if static_candidates:
                return static_candidates[0]
        else:  # "business_priority" or default
            # Registry default sort is already prioritized by B2B ranking
            pass

        selected = candidates[0]
        logger.debug(
            f"Resolved provider '{selected.provider_id}' for capability '{capability}' using policy '{policy}'"
        )
        return selected
