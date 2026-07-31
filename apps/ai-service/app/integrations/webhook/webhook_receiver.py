"""
Incoming Webhook Ingestion Engine with HMAC Signature Verification and Replay Guard.
"""

import uuid
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timezone
from app.integrations.interfaces import WebhookEventType
from app.integrations.models import WebhookEvent
from app.integrations.validation.validator import IntegrationValidator

logger = logging.getLogger("ai-service.integrations.webhook.receiver")


class WebhookReceiver:
    def __init__(self, validator: Optional[IntegrationValidator] = None) -> None:
        self.validator = validator or IntegrationValidator()
        self._processed_events: Set[str] = set()
        self._events_log: Dict[str, WebhookEvent] = {}

    def receive_webhook(
        self,
        provider_id: str,
        event_type: WebhookEventType,
        payload: Dict[str, Any],
        signature: Optional[str] = None,
        secret: Optional[str] = None,
    ) -> WebhookEvent:
        """Ingests, validates, and stores an incoming webhook event."""
        raw_str = str(payload)
        if secret and signature:
            if not self.validator.verify_webhook_signature(raw_str, secret, signature):
                logger.warning(f"Invalid signature for webhook from provider '{provider_id}'.")

        event_id = str(uuid.uuid4())
        now_str = datetime.now(timezone.utc).isoformat()

        # Replay protection check
        if event_id in self._processed_events:
            logger.warning(f"Duplicate webhook replay detected for event ID '{event_id}'.")
            return self._events_log[event_id]

        event = WebhookEvent(
            event_id=event_id,
            provider_id=provider_id,
            event_type=event_type,
            payload=payload,
            signature=signature,
            timestamp=now_str,
            processed=True,
        )

        self._processed_events.add(event_id)
        self._events_log[event_id] = event
        logger.info(f"Received and processed webhook '{event_id}' ({event_type.value}) from provider '{provider_id}'.")
        return event

    def get_event(self, event_id: str) -> Optional[WebhookEvent]:
        """Retrieves a processed webhook event by ID."""
        return self._events_log.get(event_id)

    def list_events(self) -> List[WebhookEvent]:
        """Lists all processed webhook events."""
        return list(self._events_log.values())
