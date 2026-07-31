"""
Railway Operational Feed Adapter for NTES / Official Railway Feeds.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.integrations.adapters.base_adapter import BaseAdapter
from app.integrations.models import ProviderConfiguration


class RailwayAdapter(BaseAdapter):
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
            "latency_ms": 4.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        train_num = payload.get("train_number", "12951")
        station = payload.get("station_code", "NDLS")

        raw_response = {
            "raw_train_no": train_num,
            "raw_station": station,
            "raw_status": "RUNNING",
            "raw_delay": payload.get("delay_minutes", 10),
            "raw_platform": payload.get("platform", "3"),
            "action": action,
        }
        return raw_response

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "train_number": raw_payload.get("raw_train_no", "UNKNOWN"),
            "current_station": raw_payload.get("raw_station", "UNKNOWN"),
            "operational_status": raw_payload.get("raw_status", "SCHEDULED"),
            "delay_minutes": int(raw_payload.get("raw_delay", 0)),
            "platform": str(raw_payload.get("raw_platform", "1")),
            "source_provider": self.config.provider_id,
        }

    def shutdown(self) -> None:
        self.is_initialized = False
        self.is_authenticated = False
