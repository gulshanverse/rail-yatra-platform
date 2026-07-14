"""
TTL Expiration Engine for session lifetime management.
Supports sliding and absolute expiration logic.
"""

import time
from app.memory.session import ConversationSessionMetadata


class TTLEngine:
    """Manages TTL calculations, refreshes, and expiration detection."""

    @staticmethod
    def is_expired(
        metadata: ConversationSessionMetadata, absolute: bool = False
    ) -> bool:
        """
        Determines whether a session has expired.
        If absolute=True, checks age against creation time.
        Otherwise, checks age against last access time (sliding).
        """
        now = time.time()
        if absolute:
            return now > (metadata.created_at + metadata.ttl)
        return now > (metadata.last_access + metadata.ttl)

    @staticmethod
    def refresh(metadata: ConversationSessionMetadata) -> None:
        """
        Updates timestamps to refresh sliding expiration timers.
        """
        now = time.time()
        metadata.last_access = now
        metadata.updated_at = now

    @staticmethod
    def run_cleanup_extension_point() -> None:
        """
        Reserved extension point for future background worker daemons.
        To be implemented in future batches.
        """
        pass
