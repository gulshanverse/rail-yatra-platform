# app/integration/auth/vault.py
import os
import logging
from app.integration.interfaces import ICredentialVault

logger = logging.getLogger("ai-service.integration.auth.vault")


class CredentialVault(ICredentialVault):
    def __init__(self, backend_type: str = "env"):
        self.backend_type = backend_type
        # Local mock storage for secrets if not set in environment
        self._mock_secrets = {
            "CONFIRMTKT_API_KEY": "mock-confirmtkt-key-xyz",
            "MAPMYINDIA_CLIENT_SECRET": "mock-mapmyindia-secret-123",
            "OPENWEATHER_API_KEY": "mock-openweather-key-abc",
            "SMS_GUPSHUP_API_KEY": "mock-gupshup-api-key-999",
        }

    async def get_secret(self, key: str) -> str:
        """
        Retrieves secure API keys and certificates, preventing code exposure.
        """
        # Attempt to read from OS environment
        secret = os.getenv(key)
        if secret:
            return secret

        # Fallback to local mock vault variables for sandbox/testing runs
        if key in self._mock_secrets:
            logger.debug(f"Retrieved secret {key} from Local Mock Vault")
            return self._mock_secrets[key]

        logger.warning(f"Secret key {key} not found in environment or Mock Vault.")
        return ""
