"""
Session management, key generation, and state machine transitions
for the RailYatra AI short-term memory engine.
"""

import time
from typing import Dict, Any, Optional, Set
from pydantic import BaseModel, Field

# Valid states
STATE_CREATED = "CREATED"
STATE_ACTIVE = "ACTIVE"
STATE_IDLE = "IDLE"
STATE_LOCKED = "LOCKED"
STATE_EXPIRED = "EXPIRED"
STATE_RECOVERING = "RECOVERING"
STATE_DELETED = "DELETED"

# Transition validation mapping
VALID_TRANSITIONS: Dict[str, Set[str]] = {
    STATE_CREATED: {STATE_ACTIVE, STATE_DELETED},
    STATE_ACTIVE: {STATE_LOCKED, STATE_IDLE, STATE_EXPIRED, STATE_DELETED},
    STATE_IDLE: {STATE_ACTIVE, STATE_EXPIRED, STATE_DELETED},
    STATE_LOCKED: {STATE_ACTIVE, STATE_DELETED},
    STATE_EXPIRED: {STATE_DELETED, STATE_RECOVERING},
    STATE_RECOVERING: {STATE_ACTIVE, STATE_DELETED},
    STATE_DELETED: set(),
}


class SessionKeyGenerator:
    """Centralized naming strategy for Redis keys."""

    @staticmethod
    def get_session_key(user_id: str, session_id: str) -> str:
        return f"memory:user:{user_id}:session:{session_id}"

    @staticmethod
    def get_meta_key(session_id: str) -> str:
        return f"memory:meta:{session_id}"

    @staticmethod
    def get_lock_key(session_id: str) -> str:
        return f"memory:lock:{session_id}"

    @staticmethod
    def get_index_key(user_id: str) -> str:
        return f"memory:index:{user_id}"

    @staticmethod
    def get_ttl_key(session_id: str) -> str:
        return f"memory:ttl:{session_id}"


class ConversationSessionMetadata(BaseModel):
    """Encapsulates administrative session metadata and operations."""

    user_id: str
    session_id: str
    conversation_id: str
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)
    last_access: float = Field(default_factory=time.time)
    message_count: int = 0
    token_count: int = 0
    memory_version: int = 1
    ttl: int = 86400
    feature_flags: Dict[str, Any] = Field(default_factory=dict)
    session_state: str = STATE_CREATED
    last_operation_id: Optional[str] = None  # To enforce idempotency


class ConversationSessionManager:
    """Manages session metadata updates and state transitions."""

    @staticmethod
    def create_metadata(
        user_id: str,
        session_id: str,
        conversation_id: str,
        ttl: int = 86400,
        feature_flags: Dict[str, Any] = None,
    ) -> ConversationSessionMetadata:
        return ConversationSessionMetadata(
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            ttl=ttl,
            feature_flags=feature_flags or {},
            session_state=STATE_CREATED,
        )

    @staticmethod
    def transition_state(metadata: ConversationSessionMetadata, new_state: str) -> None:
        """Validates and applies the session state transition."""
        from_state = metadata.session_state
        if from_state == new_state:
            return

        allowed_next = VALID_TRANSITIONS.get(from_state, set())
        if new_state not in allowed_next:
            raise ValueError(
                f"Illegal state transition from {from_state} to {new_state}"
            )

        metadata.session_state = new_state
        metadata.updated_at = time.time()
