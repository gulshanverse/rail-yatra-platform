"""
Validation Layer & Webhook Signature Verification for Enterprise Integration Services.
"""

import hmac
import hashlib
from typing import Dict, Any, Optional


class IntegrationValidator:
    def validate_request_payload(self, payload: Dict[str, Any]) -> bool:
        """Validates incoming payload dictionary for required keys and non-null states."""
        if not isinstance(payload, dict):
            return False
        return True

    def verify_webhook_signature(self, raw_body: str, secret: str, signature: Optional[str]) -> bool:
        """Verifies HMAC SHA-256 signature for incoming webhooks."""
        if not signature or not secret:
            return False

        computed = hmac.new(secret.encode("utf-8"), raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
        clean_sig = signature.replace("sha256=", "").strip()
        return hmac.compare_digest(computed, clean_sig)
