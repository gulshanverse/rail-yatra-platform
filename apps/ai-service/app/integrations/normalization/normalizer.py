"""
Response Payload Normalization Layer for Enterprise Integration Services.
"""

from typing import Dict, Any
from app.integrations.interfaces import IntegrationDomain


class PayloadNormalizer:
    def normalize_payload(self, domain: IntegrationDomain, provider_id: str, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalizes external raw payloads into standardized internal domain representations."""
        if not raw_data:
            return {"domain": domain.value, "provider_id": provider_id, "normalized": False}

        normalized = {"domain": domain.value, "provider_id": provider_id, "normalized": True}

        if domain == IntegrationDomain.RAILWAY:
            normalized.update({
                "train_number": str(raw_data.get("train_number") or raw_data.get("raw_train_no") or "UNKNOWN"),
                "current_station": str(raw_data.get("current_station") or raw_data.get("raw_station") or "UNKNOWN"),
                "delay_minutes": int(raw_data.get("delay_minutes") or raw_data.get("raw_delay") or 0),
                "platform": str(raw_data.get("platform") or raw_data.get("raw_platform") or "1"),
            })
        elif domain == IntegrationDomain.WEATHER:
            normalized.update({
                "station_code": str(raw_data.get("station_code") or "UNKNOWN"),
                "condition": str(raw_data.get("weather_condition") or raw_data.get("condition") or "CLEAR"),
                "journey_delay_risk": bool(raw_data.get("journey_delay_risk", False)),
            })
        elif domain == IntegrationDomain.MAPS:
            normalized.update({
                "nearest_station": str(raw_data.get("nearest_station") or raw_data.get("nearest_station_code") or "NDLS"),
                "distance_km": float(raw_data.get("distance_km") or 0.0),
                "travel_time_minutes": int(raw_data.get("travel_time_minutes") or raw_data.get("estimated_drive_mins") or 0),
            })
        elif domain == IntegrationDomain.PAYMENTS:
            normalized.update({
                "transaction_id": str(raw_data.get("transaction_id") or raw_data.get("gateway_txn_id") or "TXN_000"),
                "payment_gateway": str(raw_data.get("payment_gateway") or raw_data.get("gateway") or "UNKNOWN"),
                "payment_status": str(raw_data.get("payment_status") or raw_data.get("raw_status") or "SUCCESS"),
                "amount": float(raw_data.get("amount") or raw_data.get("amount_inr") or 0.0),
            })
        elif domain == IntegrationDomain.NOTIFICATIONS:
            normalized.update({
                "dispatch_id": str(raw_data.get("dispatch_id") or "DISP_000"),
                "channel": str(raw_data.get("channel") or "PUSH"),
                "delivery_status": str(raw_data.get("delivery_status") or raw_data.get("raw_delivery_status") or "DELIVERED"),
            })
        else:
            normalized.update(raw_data)

        return normalized
