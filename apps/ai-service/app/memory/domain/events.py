"""
Domain Events for Milestone 6.5 AI Memory Platform.
Immutable events emitted by aggregate roots upon state mutations.
"""

from dataclasses import dataclass, field
import time
import uuid
from typing import Dict, Any


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events in the AI Memory Platform."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    event_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp,
            "event_version": self.event_version,
        }


@dataclass(frozen=True)
class MemoryCreatedEvent(DomainEvent):
    """Emitted when a new memory entry is recorded."""

    memory_id: str = ""
    traveler_id: str = ""
    category: str = "LONG_TERM"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "memory_id": self.memory_id,
                "traveler_id": self.traveler_id,
                "category": self.category,
                "details": self.details,
            }
        )
        return base


@dataclass(frozen=True)
class PreferenceUpdatedEvent(DomainEvent):
    """Emitted when traveler seating, berth, or class preferences are updated."""

    traveler_id: str = ""
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "updated_fields": self.updated_fields,
            }
        )
        return base


@dataclass(frozen=True)
class ConsentGrantedEvent(DomainEvent):
    """Emitted when a traveler explicitly opts in to memory processing."""

    traveler_id: str = ""
    consent_scope: str = "FULL_MEMORY_PERSONALIZATION"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "consent_scope": self.consent_scope,
            }
        )
        return base


@dataclass(frozen=True)
class ConsentWithdrawnEvent(DomainEvent):
    """Emitted when a traveler revokes memory consent, initiating right-to-be-forgotten."""

    traveler_id: str = ""
    reason: str = "USER_REQUEST"

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "reason": self.reason,
            }
        )
        return base


@dataclass(frozen=True)
class MemoryPurgedEvent(DomainEvent):
    """Emitted after absolute erasure of traveler records."""

    traveler_id: str = ""
    records_purged_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "records_purged_count": self.records_purged_count,
            }
        )
        return base


@dataclass(frozen=True)
class JourneySagaResumedEvent(DomainEvent):
    """Emitted when an interrupted multi-session booking saga is reloaded."""

    saga_id: str = ""
    traveler_id: str = ""
    resumed_step: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "saga_id": self.saga_id,
                "traveler_id": self.traveler_id,
                "resumed_step": self.resumed_step,
            }
        )
        return base


@dataclass(frozen=True)
class PreferenceConflictDetectedEvent(DomainEvent):
    """Emitted when newly observed choices conflict with historical preferences."""

    traveler_id: str = ""
    conflicting_field: str = ""
    old_value: Any = None
    new_value: Any = None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "conflicting_field": self.conflicting_field,
                "old_value": self.old_value,
                "new_value": self.new_value,
            }
        )
        return base
