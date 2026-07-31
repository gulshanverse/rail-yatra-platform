"""
Multi-Channel Notification Integration Adapter (Email, SMS, WhatsApp, Push).
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.integrations.adapters.base_adapter import BaseAdapter
from app.integrations.models import ProviderConfiguration


class NotificationAdapter(BaseAdapter):
    def __init__(self, config: ProviderConfiguration) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.is_initialized = True

    def authenticate(self) -> bool:
        self.is_authenticated = bool(self.config.api_key)
        return self.is_authenticated

    def health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY" if self.is_initialized else "UNINITIALIZED",
            "provider_id": self.config.provider_id,
            "latency_ms": 3.1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        channel = payload.get("channel", "WHATSAPP")
        recipient = payload.get("recipient", "+919876543210")
        msg = payload.get("message", "Test alert")
        return {
            "dispatch_id": "DISP_554433",
            "channel": channel,
            "recipient": recipient,
            "raw_delivery_status": "DELIVERED",
            "message_body": msg,
        }

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "dispatch_id": raw_payload.get("dispatch_id", "UNKNOWN"),
            "channel": raw_payload.get("channel", "PUSH"),
            "delivery_status": raw_payload.get("raw_delivery_status", "DELIVERED"),
            "recipient": raw_payload.get("recipient", "UNKNOWN"),
            "source_provider": self.config.provider_id,
        }

    def shutdown(self) -> None:
        self.is_initialized = False
        self.is_authenticated = False
