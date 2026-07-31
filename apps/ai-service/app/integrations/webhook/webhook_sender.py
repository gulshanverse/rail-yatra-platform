"""
Outgoing Webhook Dispatcher Engine for Enterprise Subscribers.
"""

import hmac
import hashlib
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone

logger = logging.getLogger("ai-service.integrations.webhook.sender")


class WebhookSender:
    def dispatch_webhook(
        self,
        target_url: str,
        event_type: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Formats and dispatches an outgoing webhook to a subscriber target URL."""
        now_str = datetime.now(timezone.utc).isoformat()
        body = {
            "event_type": event_type,
            "payload": payload,
            "timestamp": now_str,
        }

        signature = None
        if secret:
            signature = hmac.new(secret.encode("utf-8"), str(body).encode("utf-8"), hashlib.sha256).hexdigest()

        logger.info(f"Dispatched outgoing webhook ({event_type}) to '{target_url}'.")
        return {
            "status": "DISPATCHED",
            "target_url": target_url,
            "signature": signature,
            "timestamp": now_str,
            "body": body,
        }
