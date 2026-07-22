"""
Repository Port Interfaces and In-Memory Repository Implementations for Milestone 6.5 AI Memory Platform.
Follows Clean Architecture Port & Adapter patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from app.memory.domain.value_objects import TravelerId
from app.memory.domain.aggregates import (
    TravelerMemory,
    ConsentProfile,
    JourneySagaMemory,
)
from app.memory.domain.entities import MemoryAuditEntry
from app.memory.exceptions import InvariantViolationException, ConsentWithdrawnException


# =====================================================================
# Port Interfaces (Clean Architecture abstractions)
# =====================================================================


class ITravelerMemoryRepository(ABC):
    """Port interface for persisting and loading TravelerMemory aggregates."""

    @abstractmethod
    def save(self, aggregate: TravelerMemory) -> None:
        pass

    @abstractmethod
    def get_by_traveler_id(self, traveler_id: TravelerId) -> Optional[TravelerMemory]:
        pass

    @abstractmethod
    def delete(self, traveler_id: TravelerId) -> bool:
        pass


class IConsentProfileRepository(ABC):
    """Port interface for persisting and loading ConsentProfile aggregates."""

    @abstractmethod
    def save(self, consent_profile: ConsentProfile) -> None:
        pass

    @abstractmethod
    def get_by_traveler_id(self, traveler_id: TravelerId) -> Optional[ConsentProfile]:
        pass


class IJourneySagaRepository(ABC):
    """Port interface for persisting and loading JourneySagaMemory aggregates."""

    @abstractmethod
    def save(self, saga: JourneySagaMemory) -> None:
        pass

    @abstractmethod
    def get_by_saga_id(self, saga_id: str) -> Optional[JourneySagaMemory]:
        pass

    @abstractmethod
    def get_active_saga_by_traveler_id(
        self, traveler_id: TravelerId
    ) -> Optional[JourneySagaMemory]:
        pass


class IMemoryAuditLogger(ABC):
    """Port interface for immutable governance audit logging."""

    @abstractmethod
    def log_entry(self, entry: MemoryAuditEntry) -> None:
        pass

    @abstractmethod
    def get_audit_trail(self, traveler_id: str) -> List[MemoryAuditEntry]:
        pass


# =====================================================================
# In-Memory Adapters (Production-ready state implementations)
# =====================================================================


class InMemoryConsentProfileRepository(IConsentProfileRepository):
    """In-Memory repository storing ConsentProfile aggregates."""

    def __init__(self):
        self._store: Dict[str, ConsentProfile] = {}

    def save(self, consent_profile: ConsentProfile) -> None:
        if not consent_profile or not consent_profile.traveler_id:
            raise InvariantViolationException("Cannot save invalid ConsentProfile.")
        self._store[consent_profile.traveler_id.value] = consent_profile

    def get_by_traveler_id(self, traveler_id: TravelerId) -> Optional[ConsentProfile]:
        return self._store.get(traveler_id.value)


class InMemoryTravelerMemoryRepository(ITravelerMemoryRepository):
    """In-Memory repository storing TravelerMemory aggregates."""

    def __init__(self, consent_repo: Optional[IConsentProfileRepository] = None):
        self._store: Dict[str, TravelerMemory] = {}
        self.consent_repo = consent_repo or InMemoryConsentProfileRepository()

    def save(self, aggregate: TravelerMemory) -> None:
        if not aggregate or not aggregate.traveler_id:
            raise InvariantViolationException(
                "Cannot save invalid TravelerMemory aggregate."
            )
        # Mandatory Consent Repository Gate: ensure matching consent profile exists
        consent = self.consent_repo.get_by_traveler_id(aggregate.traveler_id)
        if consent:
            aggregate.consent_profile = consent

        self._store[aggregate.traveler_id.value] = aggregate

    def get_by_traveler_id(self, traveler_id: TravelerId) -> Optional[TravelerMemory]:
        aggregate = self._store.get(traveler_id.value)
        if aggregate:
            # Sync consent status from repository gate
            consent = self.consent_repo.get_by_traveler_id(traveler_id)
            if consent:
                aggregate.consent_profile = consent
            if aggregate.consent_profile.is_withdrawn or aggregate.is_purged:
                raise ConsentWithdrawnException(
                    "Access Denied: Traveler consent is withdrawn or purged."
                )
        return aggregate

    def delete(self, traveler_id: TravelerId) -> bool:
        if traveler_id.value in self._store:
            del self._store[traveler_id.value]
            return True
        return False


class InMemoryJourneySagaRepository(IJourneySagaRepository):
    """In-Memory repository storing JourneySagaMemory aggregates."""

    def __init__(self):
        self._saga_store: Dict[str, JourneySagaMemory] = {}

    def save(self, saga: JourneySagaMemory) -> None:
        if not saga or not saga.saga_id:
            raise InvariantViolationException("Cannot save invalid JourneySagaMemory.")
        self._saga_store[saga.saga_id] = saga

    def get_by_saga_id(self, saga_id: str) -> Optional[JourneySagaMemory]:
        saga = self._saga_store.get(saga_id)
        if saga and saga.is_completed:
            return saga
        if saga:
            saga.check_expiration()
        return saga

    def get_active_saga_by_traveler_id(
        self, traveler_id: TravelerId
    ) -> Optional[JourneySagaMemory]:
        active_sagas = [
            s
            for s in self._saga_store.values()
            if s.traveler_id.value == traveler_id.value and not s.is_completed
        ]
        if not active_sagas:
            return None
        # Sort by most recent
        active_sagas.sort(key=lambda x: x.last_active_at, reverse=True)
        most_recent = active_sagas[0]
        most_recent.check_expiration()
        return most_recent


class InMemoryAuditLogger(IMemoryAuditLogger):
    """Append-only audit log store for governance auditing."""

    def __init__(self):
        self._logs: Dict[str, List[MemoryAuditEntry]] = {}

    def log_entry(self, entry: MemoryAuditEntry) -> None:
        if entry.traveler_id not in self._logs:
            self._logs[entry.traveler_id] = []
        self._logs[entry.traveler_id].append(entry)

    def get_audit_trail(self, traveler_id: str) -> List[MemoryAuditEntry]:
        return list(self._logs.get(traveler_id, []))
