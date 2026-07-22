"""
Infrastructure Repositories for Milestone 6.6 AI Response Composer Platform.
In-memory repository implementations adhering to Clean Architecture ports.
"""

from typing import Dict, List, Optional, Any
import time

from app.composer.domain.aggregates import ResponseComposition, ConversationSession
from app.composer.domain.repositories import (
    IResponseCompositionRepository,
    IConversationSessionRepository,
    IComposerAuditLogger,
)


class InMemoryResponseCompositionRepository(IResponseCompositionRepository):
    """In-memory adapter implementing IResponseCompositionRepository for testing & dev."""

    def __init__(self):
        self._store: Dict[str, ResponseComposition] = {}

    def save(self, composition: ResponseComposition) -> None:
        self._store[composition.composition_id] = composition

    def get_by_id(self, composition_id: str) -> Optional[ResponseComposition]:
        return self._store.get(composition_id)

    def get_by_session_id(self, session_id: str) -> List[ResponseComposition]:
        return [c for c in self._store.values() if c.session_id == session_id]


class InMemoryConversationSessionRepository(IConversationSessionRepository):
    """In-memory adapter implementing IConversationSessionRepository."""

    def __init__(self):
        self._store: Dict[str, ConversationSession] = {}

    def save(self, session: ConversationSession) -> None:
        self._store[session.session_id] = session

    def get_by_id(self, session_id: str) -> Optional[ConversationSession]:
        return self._store.get(session_id)

    def get_active_session_by_traveler(self, traveler_id: str) -> Optional[ConversationSession]:
        sessions = [s for s in self._store.values() if s.traveler_id == traveler_id]
        if not sessions:
            return None
        return max(sessions, key=lambda s: s.last_active_at)


class InMemoryComposerAuditLogger(IComposerAuditLogger):
    """In-memory adapter implementing IComposerAuditLogger."""

    def __init__(self):
        self._logs: List[Dict[str, Any]] = []

    def log_event(
        self,
        event_type: str,
        session_id: str,
        traveler_id: str,
        details: Dict[str, Any],
    ) -> None:
        entry = {
            "event_type": event_type,
            "session_id": session_id,
            "traveler_id": traveler_id,
            "details": details,
            "timestamp": time.time(),
        }
        self._logs.append(entry)

    def get_audit_trail(self, traveler_id: str) -> List[Dict[str, Any]]:
        return [entry for entry in self._logs if entry["traveler_id"] == traveler_id]
