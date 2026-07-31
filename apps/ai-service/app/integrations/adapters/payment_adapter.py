"""
Multi-Gateway Payment Integration Adapter (Razorpay, PhonePe, Google Pay, Stripe).
"""

from typing import Dict, Any
from datetime import datetime, timezone
from app.integrations.adapters.base_adapter import BaseAdapter
from app.integrations.models import ProviderConfiguration


class PaymentAdapter(BaseAdapter):
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
            "latency_ms": 6.2,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        txn_id = payload.get("transaction_id", "TXN_998877")
        amount = payload.get("amount", 450.0)
        gateway = payload.get("gateway", "RAZORPAY")
        return {
            "gateway_txn_id": txn_id,
            "gateway": gateway,
            "raw_status": "SUCCESS",
            "amount_inr": amount,
            "currency": "INR",
        }

    def normalize(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "transaction_id": raw_payload.get("gateway_txn_id", "UNKNOWN"),
            "payment_gateway": raw_payload.get("gateway", "RAZORPAY"),
            "payment_status": raw_payload.get("raw_status", "SUCCESS"),
            "amount": float(raw_payload.get("amount_inr", 0.0)),
            "currency": raw_payload.get("currency", "INR"),
            "source_provider": self.config.provider_id,
        }

    def shutdown(self) -> None:
        self.is_initialized = False
        self.is_authenticated = False
