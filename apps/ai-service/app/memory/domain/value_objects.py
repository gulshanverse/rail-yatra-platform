"""
Value Objects for Milestone 6.5 AI Memory Platform Domain.
Immutable, self-validating value objects following DDD principles.
"""

from dataclasses import dataclass, field
from enum import Enum
import time
import uuid
from typing import Optional

from app.memory.exceptions import InvariantViolationException


class MemoryCategory(str, Enum):
    """Enterprise Memory Taxonomy categories."""

    WORKING = "WORKING"
    SHORT_TERM = "SHORT_TERM"
    LONG_TERM = "LONG_TERM"
    PREFERENCE = "PREFERENCE"
    JOURNEY = "JOURNEY"
    CONSENT = "CONSENT"


class ConsentStatusEnum(str, Enum):
    """Consent status enumeration values."""

    GRANTED = "GRANTED"
    WITHDRAWN = "WITHDRAWN"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class BerthPreferenceEnum(str, Enum):
    """Railway berth seating preference enumeration."""

    LOWER = "LOWER"
    UPPER = "UPPER"
    MIDDLE = "MIDDLE"
    SIDE_LOWER = "SIDE_LOWER"
    SIDE_UPPER = "SIDE_UPPER"
    WINDOW = "WINDOW"
    NO_PREFERENCE = "NO_PREFERENCE"


@dataclass(frozen=True)
class TravelerId:
    """Immutable domain value object representing a unique traveler identity."""

    value: str

    def __post_init__(self):
        if (
            not self.value
            or not isinstance(self.value, str)
            or len(self.value.strip()) == 0
        ):
            raise InvariantViolationException(
                "TravelerId cannot be empty or non-string."
            )


@dataclass(frozen=True)
class MemoryId:
    """Immutable domain value object for memory entry identity."""

    value: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise InvariantViolationException("MemoryId must be a valid string UUID.")


@dataclass(frozen=True)
class ConfidenceScore:
    """Value Object representing statistical confidence (0.00 to 1.00)."""

    score: float

    def __post_init__(self):
        if not isinstance(self.score, (int, float)) or not (
            0.0 <= float(self.score) <= 1.0
        ):
            raise InvariantViolationException(
                f"ConfidenceScore must be between 0.0 and 1.0. Got: {self.score}"
            )


@dataclass(frozen=True)
class RetentionPolicy:
    """Value Object defining lifecycle retention limits."""

    idle_expiration_days: int = 365
    max_age_days: int = 730
    auto_purge_on_withdraw: bool = True

    def __post_init__(self):
        if self.idle_expiration_days <= 0 or self.max_age_days <= 0:
            raise InvariantViolationException(
                "RetentionPolicy day limits must be positive integers."
            )
        if self.idle_expiration_days > self.max_age_days:
            raise InvariantViolationException(
                "idle_expiration_days cannot exceed max_age_days."
            )


@dataclass(frozen=True)
class ConsentStatus:
    """Value Object encapsulating opt-in state and privacy metadata."""

    status: ConsentStatusEnum
    granted_at: Optional[float] = None
    withdrawn_at: Optional[float] = None
    consent_scope: str = "FULL_MEMORY_PERSONALIZATION"

    def __post_init__(self):
        if not isinstance(self.status, ConsentStatusEnum):
            raise InvariantViolationException(
                f"Invalid consent status type: {type(self.status)}"
            )

    @property
    def is_active(self) -> bool:
        return self.status == ConsentStatusEnum.GRANTED


@dataclass(frozen=True)
class RouteFrequency:
    """Value Object pairing origin-destination travel count."""

    origin_station: str
    destination_station: str
    trip_count: int = 1
    last_traveled_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.origin_station or not self.destination_station:
            raise InvariantViolationException(
                "Origin and Destination stations cannot be empty."
            )
        if self.trip_count < 1:
            raise InvariantViolationException("trip_count must be at least 1.")


@dataclass(frozen=True)
class BerthPreference:
    """Value Object representing seating choice."""

    preference: BerthPreferenceEnum = BerthPreferenceEnum.NO_PREFERENCE

    def __post_init__(self):
        if not isinstance(self.preference, BerthPreferenceEnum):
            raise InvariantViolationException(
                f"Invalid BerthPreference enum: {self.preference}"
            )
