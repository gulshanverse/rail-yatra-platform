"""
Domain Repository Ports for Milestone 6.6 AI Response Composer Platform.
Clean Architecture abstract interfaces defining contracts for persistence and upstream intelligence feeds.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from app.composer.domain.aggregates import (
    ResponseComposition,
    ConversationSession,
)


class IResponseCompositionRepository(ABC):
    """Abstract Repository Port for ResponseComposition aggregate root persistence."""

    @abstractmethod
    def save(self, composition: ResponseComposition) -> None:
        """Persists a synthesized ResponseComposition aggregate."""
        pass

    @abstractmethod
    def get_by_id(self, composition_id: str) -> Optional[ResponseComposition]:
        """Retrieves composition aggregate by ID."""
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: str) -> List[ResponseComposition]:
        """Retrieves all compositions for a given session."""
        pass


class IConversationSessionRepository(ABC):
    """Abstract Repository Port for ConversationSession multi-turn context tracking."""

    @abstractmethod
    def save(self, session: ConversationSession) -> None:
        """Persists or updates a ConversationSession aggregate."""
        pass

    @abstractmethod
    def get_by_id(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieves session aggregate by ID."""
        pass

    @abstractmethod
    def get_active_session_by_traveler(self, traveler_id: str) -> Optional[ConversationSession]:
        """Retrieves active conversation session for traveler."""
        pass


class IComposerAuditLogger(ABC):
    """Abstract Audit Logger Port for immutable, hash-verified composition audit records."""

    @abstractmethod
    def log_event(
        self,
        event_type: str,
        session_id: str,
        traveler_id: str,
        details: Dict[str, Any],
    ) -> None:
        """Logs an append-only audit trail entry."""
        pass

    @abstractmethod
    def get_audit_trail(self, traveler_id: str) -> List[Dict[str, Any]]:
        """Retrieves audit trail entries for traveler."""
        pass


class IUpstreamIntelligencePort(ABC):
    """Abstract Port for gathering multi-source intelligence from upstream AI engines."""

    @abstractmethod
    def fetch_memory_context(self, traveler_id: str) -> Dict[str, Any]:
        """Fetches traveler profile, preferences, and DPDP consent state from Memory Platform (M6.5)."""
        pass

    @abstractmethod
    def fetch_journey_plan(self, origin: str, destination: str) -> Dict[str, Any]:
        """Fetches multi-modal itinerary plans from Journey Planner Engine."""
        pass

    @abstractmethod
    def fetch_prediction_odds(self, pnr_or_train: str) -> Dict[str, Any]:
        """Fetches waitlist confirmation odds and delay forecasts from Prediction Engine."""
        pass

    @abstractmethod
    def fetch_knowledge_rules(self, query: str) -> Dict[str, Any]:
        """Fetches grounded IRCTC rules and refund policies from Knowledge RAG Base."""
        pass

    @abstractmethod
    def fetch_operational_status(self, train_number: str) -> Dict[str, Any]:
        """Fetches live running status and station feeds from Railway Operations integration."""
        pass
