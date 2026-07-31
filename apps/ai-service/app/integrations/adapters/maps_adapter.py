"""
Maps & Geolocation Station Navigation Adapter.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.integrations.adapters.base_adapter import BaseAdapter
from app.integrations.models import ProviderConfiguration


class MapsAdapter(BaseAdapter):
    def __init__(self, config: ProviderConfiguration) -> None:
        super().__init__(config)

    def initialize(self) -> None:
        self.is_initialized = True

    def authenticate(self) -> bool:
        self.is_authenticated = True
        return self.is_authenticated

    def health(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY" if self.is_initialized else "UNINITIALIZED",
            "provider_id": self.config.provider_id,
            "latency_ms": 5.1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        lat = payload.get("latitude", 28.6139)
        lng = payload.get("longitude", 77.2090)
        return {
            "query_lat": lat,
            "query_lng": lng,
            "nearest_station_code": "NDLS",
            "distance_km": 1.2,
            "estimated_drive_mins": 8,
        }

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "nearest_station": raw_payload.get("nearest_station_code", "NDLS"),
            "distance_km": float(raw_payload.get("distance_km", 0.0)),
            "travel_time_minutes": int(raw_payload.get("estimated_drive_mins", 0)),
            "source_provider": self.config.provider_id,
        }

    def shutdown(self) -> None:
        self.is_initialized = False
        self.is_authenticated = False
