"""
Integration Gateway Entry Point Facade for Enterprise Integrations Platform.
"""

import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.integrations.interfaces import IntegrationDomain, WebhookEventType
from app.integrations.models import IntegrationRequest, IntegrationResponse, WebhookEvent
from app.integrations.configuration.provider_config import ProviderConfigManager
from app.integrations.registry.provider_registry import ProviderRegistry
from app.integrations.orchestration.provider_orchestrator import ProviderOrchestrator
from app.integrations.webhook.webhook_receiver import WebhookReceiver
from app.integrations.webhook.webhook_sender import WebhookSender
from app.integrations.monitoring.provider_monitor import ProviderMonitor
from app.integrations.adapters.railway_adapter import RailwayAdapter
from app.integrations.adapters.weather_adapter import WeatherAdapter
from app.integrations.adapters.maps_adapter import MapsAdapter
from app.integrations.adapters.payment_adapter import PaymentAdapter
from app.integrations.adapters.notification_adapter import NotificationAdapter

logger = logging.getLogger("ai-service.integrations.gateway")


class IntegrationGateway:
    def __init__(self) -> None:
        self.config_manager = ProviderConfigManager()
        self.registry = ProviderRegistry()
        self.orchestrator = ProviderOrchestrator(registry=self.registry)
        self.webhook_receiver = WebhookReceiver()
        self.webhook_sender = WebhookSender()
        self.monitor = ProviderMonitor(registry=self.registry)

        self._bootstrap_adapters()

    def _bootstrap_adapters(self) -> None:
        """Initializes and registers standard domain provider adapters."""
        configs = self.config_manager.list_configs()

        adapter_factories = {
            "railway_ntes": (RailwayAdapter, "NTES Official Railway Feed"),
            "weather_openmeteo": (WeatherAdapter, "OpenMeteo Weather Intelligence"),
            "maps_google": (MapsAdapter, "Google Maps Station Navigation"),
            "payment_razorpay": (PaymentAdapter, "Razorpay Gateway Expansion"),
            "notification_multi": (NotificationAdapter, "Multi-Channel Notification Dispatcher"),
        }

        for pid, (cls, name) in adapter_factories.items():
            cfg = configs.get(pid)
            if cfg:
                self.registry.register_provider(
                    provider_id=pid,
                    name=name,
                    domain=cfg.domain,
                    configuration=cfg,
                )
                adapter_instance = cls(cfg)
                self.orchestrator.register_adapter(pid, adapter_instance)

    def execute_integration(self, provider_id: str, action: str, payload: Dict[str, Any]) -> IntegrationResponse:
        """Entry point for executing third-party integration requests."""
        provider = self.registry.get_provider(provider_id)
        domain = provider.domain if provider else IntegrationDomain.RAILWAY

        request = IntegrationRequest(
            request_id=f"req_{uuid.uuid4().hex[:8]}",
            provider_id=provider_id,
            domain=domain,
            action=action,
            payload=payload,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        return self.orchestrator.execute_request(request)

    def process_incoming_webhook(
        self,
        provider_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> WebhookEvent:
        """Processes incoming webhooks via WebhookReceiver."""
        return self.webhook_receiver.receive_webhook(
            provider_id=provider_id,
            event_type=event_type,
            payload=payload,
            signature=signature,
            secret=secret,
        )

    def dispatch_outgoing_webhook(self, target_url: str, event_type: str, payload: Dict[str, Any], secret: Optional[str] = None) -> Dict[str, Any]:
        """Dispatches an outgoing webhook to a subscriber via WebhookSender."""
        return self.webhook_sender.dispatch_webhook(target_url, event_type, payload, secret)

    def get_system_health(self) -> Dict[str, Any]:
        """Returns unified system health for all enterprise integrations."""
        return self.monitor.check_health()
