# app/integration/registry.py
import logging
from typing import List, Dict
from app.integration.interfaces import IProviderRegistry
from app.integration.models import ProviderMetadata, RateLimitConfig

logger = logging.getLogger("ai-service.integration.registry")


class ProviderRegistry(IProviderRegistry):
    def __init__(self):
        # Initialize default providers catalog as outlined in Discovery
        self._providers: Dict[str, ProviderMetadata] = {}
        self._initialize_catalog()

    def _initialize_catalog(self):
        # ConfirmTkt GDS
        self.register_provider(
            ProviderMetadata(
                provider_id="confirmtkt_gds",
                name="ConfirmTkt GDS Partner API",
                version="v1",
                status="active",
                capabilities=["pnr_lookup", "coach_position", "platform_info"],
                auth_method="oauth2",
                rate_limits=RateLimitConfig(
                    requests_per_minute=60,
                    burst_limit=100,
                    daily_quota=10000,
                    monthly_budget_usd=1000.0,
                ),
                sla_availability=0.999,
                expected_latency_ms=400,
                cost_per_query_usd=0.003,
                priority=1,
                region="IN",
            )
        )

        # RapidAPI Indian Railways
        self.register_provider(
            ProviderMetadata(
                provider_id="rapidapi_railway",
                name="RapidAPI Indian Railways API",
                version="v1",
                status="active",
                capabilities=["pnr_lookup", "seat_availability"],
                auth_method="apikey",
                rate_limits=RateLimitConfig(
                    requests_per_minute=50,
                    burst_limit=75,
                    daily_quota=5000,
                    monthly_budget_usd=500.0,
                ),
                sla_availability=0.98,
                expected_latency_ms=1000,
                cost_per_query_usd=0.010,
                priority=2,
                region="IN",
            )
        )

        # NTES CRIS Direct Gateway
        self.register_provider(
            ProviderMetadata(
                provider_id="ntes_cris",
                name="NTES CRIS Direct Gateway",
                version="v2",
                status="active",
                capabilities=["live_train_status"],
                auth_method="mtls",
                rate_limits=RateLimitConfig(
                    requests_per_minute=120,
                    burst_limit=200,
                    daily_quota=50000,
                    monthly_budget_usd=0.0,
                ),
                sla_availability=0.995,
                expected_latency_ms=200,
                cost_per_query_usd=0.000,
                priority=1,
                region="IN",
            )
        )

        # ConfirmTkt Live API (Secondary Live Tracking)
        self.register_provider(
            ProviderMetadata(
                provider_id="confirmtkt_live",
                name="ConfirmTkt Live Tracking API",
                version="v1",
                status="active",
                capabilities=["live_train_status"],
                auth_method="oauth2",
                rate_limits=RateLimitConfig(
                    requests_per_minute=100,
                    burst_limit=150,
                    daily_quota=30000,
                    monthly_budget_usd=100.0,
                ),
                sla_availability=0.99,
                expected_latency_ms=450,
                cost_per_query_usd=0.001,
                priority=2,
                region="IN",
            )
        )

        # OGD India (data.gov.in)
        self.register_provider(
            ProviderMetadata(
                provider_id="static_local",
                name="Open Government Data SQLite Ingestion",
                version="v1",
                status="active",
                capabilities=[
                    "station_info",
                    "reservation_rules",
                    "railway_circulars",
                    "train_schedule",
                ],
                auth_method="none",
                rate_limits=RateLimitConfig(
                    requests_per_minute=9999,
                    burst_limit=9999,
                    daily_quota=999999,
                    monthly_budget_usd=0.0,
                ),
                sla_availability=1.0,
                expected_latency_ms=10,
                cost_per_query_usd=0.000,
                priority=1,
                region="IN",
            )
        )

        # MapmyIndia
        self.register_provider(
            ProviderMetadata(
                provider_id="mapmyindia",
                name="MapmyIndia Mappls API",
                version="v2",
                status="active",
                capabilities=["maps"],
                auth_method="oauth2",
                rate_limits=RateLimitConfig(
                    requests_per_minute=120,
                    burst_limit=150,
                    daily_quota=10000,
                    monthly_budget_usd=200.0,
                ),
                sla_availability=0.999,
                expected_latency_ms=120,
                cost_per_query_usd=0.002,
                priority=1,
                region="IN",
            )
        )

        # OpenWeatherMap
        self.register_provider(
            ProviderMetadata(
                provider_id="openweather",
                name="OpenWeatherMap Weather API",
                version="v2.5",
                status="active",
                capabilities=["weather"],
                auth_method="apikey",
                rate_limits=RateLimitConfig(
                    requests_per_minute=60,
                    burst_limit=100,
                    daily_quota=2000,
                    monthly_budget_usd=50.0,
                ),
                sla_availability=0.999,
                expected_latency_ms=150,
                cost_per_query_usd=0.001,
                priority=1,
                region="GLOBAL",
            )
        )

        # SMS Gupshup Gateway
        self.register_provider(
            ProviderMetadata(
                provider_id="sms_gupshup",
                name="SMS Gupshup Gateway",
                version="v1",
                status="active",
                capabilities=["notifications"],
                auth_method="apikey",
                rate_limits=RateLimitConfig(
                    requests_per_minute=500,
                    burst_limit=1000,
                    daily_quota=50000,
                    monthly_budget_usd=150.0,
                ),
                sla_availability=0.9999,
                expected_latency_ms=80,
                cost_per_query_usd=0.0015,
                priority=1,
                region="IN",
            )
        )

    def register_provider(self, provider: ProviderMetadata) -> None:
        self._providers[provider.provider_id] = provider
        logger.info(f"Registered provider: {provider.provider_id} ({provider.name})")

    def get_providers_for_capability(self, capability: str) -> List[ProviderMetadata]:
        matching = [
            p
            for p in self._providers.values()
            if capability in p.capabilities and p.status != "offline"
        ]
        # Sort primarily by status, then by priority rank (lower rank number is higher priority)
        matching.sort(key=lambda p: p.priority)
        return matching

    def update_provider_status(self, provider_id: str, status: str) -> None:
        if provider_id in self._providers:
            self._providers[provider_id].status = status
            logger.info(
                f"Dynamic state transition: provider '{provider_id}' is now '{status}'"
            )

    def list_all_providers(self) -> List[ProviderMetadata]:
        return list(self._providers.values())
