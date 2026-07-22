"""
Domain Entities for Milestone 6.5 AI Memory Platform.
Rich domain entities with internal identity and state management.
"""

from typing import List, Dict, Any, Optional
import time
import uuid
import hashlib

from app.memory.domain.value_objects import (
    TravelerId,
    BerthPreference,
    BerthPreferenceEnum,
    RouteFrequency,
)
from app.memory.exceptions import InvariantViolationException


class CompanionRecord:
    """Entity representing a frequent co-passenger."""

    def __init__(
        self,
        name: str,
        age: int,
        gender: str,
        relationship: str = "FAMILY",
        companion_id: Optional[str] = None,
    ):
        if not name or age <= 0 or not gender:
            raise InvariantViolationException(
                "CompanionRecord requires valid name, age > 0, and gender."
            )
        self.companion_id = companion_id or str(uuid.uuid4())
        self.name = name.strip()
        self.age = age
        self.gender = gender.upper().strip()
        self.relationship = relationship.upper().strip()

    def is_senior(self) -> bool:
        return self.age >= 60

    def to_dict(self) -> Dict[str, Any]:
        return {
            "companion_id": self.companion_id,
            "name": self.name,
            "age": self.age,
            "gender": self.gender,
            "relationship": self.relationship,
        }


class TravelerProfile:
    """Entity representing primary traveler demographics and companion associations."""

    def __init__(
        self,
        traveler_id: TravelerId,
        full_name: str,
        age: int,
        gender: str,
        profile_id: Optional[str] = None,
        companions: Optional[List[CompanionRecord]] = None,
    ):
        if not full_name or age < 0 or not gender:
            raise InvariantViolationException(
                "TravelerProfile requires valid full_name, age >= 0, and gender."
            )
        self.profile_id = profile_id or str(uuid.uuid4())
        self.traveler_id = traveler_id
        self.full_name = full_name.strip()
        self.age = age
        self.gender = gender.upper().strip()
        self.companions: List[CompanionRecord] = companions or []

    @property
    def is_senior_citizen(self) -> bool:
        return self.age >= 60

    @property
    def senior_concession_eligible(self) -> bool:
        # BR-MEM-003: Concession Eligibility verification rule
        return self.is_senior_citizen

    def add_companion(self, companion: CompanionRecord) -> None:
        # Prevent duplicate companion records
        for c in self.companions:
            if c.name.lower() == companion.name.lower() and c.age == companion.age:
                return
        self.companions.append(companion)

    def remove_companion(self, companion_id: str) -> bool:
        initial_len = len(self.companions)
        self.companions = [c for c in self.companions if c.companion_id != companion_id]
        return len(self.companions) < initial_len

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "traveler_id": self.traveler_id.value,
            "full_name": self.full_name,
            "age": self.age,
            "gender": self.gender,
            "is_senior_citizen": self.is_senior_citizen,
            "senior_concession_eligible": self.senior_concession_eligible,
            "companions": [c.to_dict() for c in self.companions],
        }


class PreferenceStore:
    """Entity storing categorized seating, berth, meal, and train class choices."""

    def __init__(
        self,
        berth_preference: BerthPreference = BerthPreference(
            BerthPreferenceEnum.NO_PREFERENCE
        ),
        preferred_class: str = "SL",
        meal_preference: str = "VEG",
        departure_window: str = "EVENING",
        preference_id: Optional[str] = None,
    ):
        self.preference_id = preference_id or str(uuid.uuid4())
        self.berth_preference = berth_preference
        self.preferred_class = preferred_class.upper().strip()
        self.meal_preference = meal_preference.upper().strip()
        self.departure_window = departure_window.upper().strip()
        self.updated_at: float = time.time()

    def update_preferences(
        self,
        berth: Optional[BerthPreference] = None,
        train_class: Optional[str] = None,
        meal: Optional[str] = None,
        window: Optional[str] = None,
    ) -> None:
        if berth is not None:
            self.berth_preference = berth
        if train_class is not None and train_class.strip():
            self.preferred_class = train_class.upper().strip()
        if meal is not None and meal.strip():
            self.meal_preference = meal.upper().strip()
        if window is not None and window.strip():
            self.departure_window = window.upper().strip()
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preference_id": self.preference_id,
            "berth_preference": self.berth_preference.preference.value,
            "preferred_class": self.preferred_class,
            "meal_preference": self.meal_preference,
            "departure_window": self.departure_window,
            "updated_at": self.updated_at,
        }


class JourneyHistory:
    """Entity tracking historical origin-destination frequency choices."""

    def __init__(
        self,
        history_id: Optional[str] = None,
        routes: Optional[List[RouteFrequency]] = None,
    ):
        self.history_id = history_id or str(uuid.uuid4())
        self.routes: List[RouteFrequency] = routes or []

    def record_trip(self, origin: str, destination: str) -> RouteFrequency:
        origin_clean = origin.upper().strip()
        dest_clean = destination.upper().strip()

        updated_routes: List[RouteFrequency] = []
        found = False
        target_rf = None

        for rf in self.routes:
            if (
                rf.origin_station == origin_clean
                and rf.destination_station == dest_clean
            ):
                target_rf = RouteFrequency(
                    origin_station=origin_clean,
                    destination_station=dest_clean,
                    trip_count=rf.trip_count + 1,
                    last_traveled_at=time.time(),
                )
                updated_routes.append(target_rf)
                found = True
            else:
                updated_routes.append(rf)

        if not found:
            target_rf = RouteFrequency(
                origin_station=origin_clean,
                destination_station=dest_clean,
                trip_count=1,
                last_traveled_at=time.time(),
            )
            updated_routes.append(target_rf)

        self.routes = updated_routes
        assert target_rf is not None
        return target_rf

    def get_frequent_routes(self, min_frequency: int = 2) -> List[RouteFrequency]:
        return [rf for rf in self.routes if rf.trip_count >= min_frequency]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "history_id": self.history_id,
            "total_routes_tracked": len(self.routes),
            "routes": [
                {
                    "origin": rf.origin_station,
                    "destination": rf.destination_station,
                    "count": rf.trip_count,
                    "last_traveled": rf.last_traveled_at,
                }
                for rf in self.routes
            ],
        }


class MemoryAuditEntry:
    """Immutable audit entry tracking memory creations, updates, queries, and purges."""

    def __init__(
        self,
        traveler_id: str,
        action: str,
        actor: str = "SYSTEM",
        details: Optional[Dict[str, Any]] = None,
        audit_id: Optional[str] = None,
        timestamp: Optional[float] = None,
    ):
        self.audit_id = audit_id or str(uuid.uuid4())
        self.traveler_id = traveler_id
        self.action = action.upper().strip()
        self.actor = actor.strip()
        self.details = details or {}
        self.timestamp = timestamp or time.time()
        self.hash_signature = self._generate_hash()

    def _generate_hash(self) -> str:
        raw = f"{self.audit_id}:{self.traveler_id}:{self.action}:{self.timestamp}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "audit_id": self.audit_id,
            "traveler_id": self.traveler_id,
            "action": self.action,
            "actor": self.actor,
            "details": self.details,
            "timestamp": self.timestamp,
            "hash_signature": self.hash_signature,
        }
