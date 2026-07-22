"""
Domain Aggregates for Milestone 6.5 AI Memory Platform.
Primary aggregate roots enforcing consistency boundaries and aggregate invariants.
"""

from typing import List, Dict, Any, Optional
import time
import uuid

from app.memory.domain.value_objects import (
    TravelerId,
    ConsentStatus,
    ConsentStatusEnum,
    RetentionPolicy,
    BerthPreference,
    RouteFrequency,
)
from app.memory.domain.entities import (
    TravelerProfile,
    PreferenceStore,
    JourneyHistory,
    CompanionRecord,
)
from app.memory.domain.events import (
    DomainEvent,
    MemoryCreatedEvent,
    PreferenceUpdatedEvent,
    ConsentGrantedEvent,
    ConsentWithdrawnEvent,
    MemoryPurgedEvent,
    JourneySagaResumedEvent,
    PreferenceConflictDetectedEvent,
)
from app.memory.domain.policies import ConflictResolutionPolicy
from app.memory.exceptions import (
    InvariantViolationException,
    ConsentMissingException,
    ConsentWithdrawnException,
    SagaExpiredException,
)


class ConsentProfile:
    """Aggregate Root managing traveler opt-in grants, privacy preferences, and purge requests."""

    def __init__(
        self,
        traveler_id: TravelerId,
        consent_status: ConsentStatus = ConsentStatus(
            ConsentStatusEnum.PENDING_VERIFICATION
        ),
        retention_policy: RetentionPolicy = RetentionPolicy(),
    ):
        if not traveler_id:
            raise InvariantViolationException(
                "ConsentProfile requires a valid TravelerId."
            )
        self.traveler_id = traveler_id
        self.consent_status = consent_status
        self.retention_policy = retention_policy
        self._domain_events: List[DomainEvent] = []

    @property
    def is_granted(self) -> bool:
        return self.consent_status.status == ConsentStatusEnum.GRANTED

    @property
    def is_withdrawn(self) -> bool:
        return self.consent_status.status == ConsentStatusEnum.WITHDRAWN

    def grant_consent(self, scope: str = "FULL_MEMORY_PERSONALIZATION") -> None:
        self.consent_status = ConsentStatus(
            status=ConsentStatusEnum.GRANTED,
            granted_at=time.time(),
            consent_scope=scope,
        )
        self._record_event(
            ConsentGrantedEvent(
                traveler_id=self.traveler_id.value,
                consent_scope=scope,
            )
        )

    def withdraw_consent(self, reason: str = "USER_REQUEST") -> None:
        self.consent_status = ConsentStatus(
            status=ConsentStatusEnum.WITHDRAWN,
            withdrawn_at=time.time(),
        )
        self._record_event(
            ConsentWithdrawnEvent(
                traveler_id=self.traveler_id.value,
                reason=reason,
            )
        )

    def _record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events


class TravelerMemory:
    """Primary Aggregate Root for Traveler Memory Intelligence."""

    def __init__(
        self,
        traveler_id: TravelerId,
        consent_profile: ConsentProfile,
        profile: Optional[TravelerProfile] = None,
        preferences: Optional[PreferenceStore] = None,
        journey_history: Optional[JourneyHistory] = None,
    ):
        # Aggregate Invariant Check
        if not traveler_id:
            raise InvariantViolationException(
                "TravelerMemory cannot exist without association to a valid TravelerId."
            )
        if (
            not consent_profile
            or consent_profile.traveler_id.value != traveler_id.value
        ):
            raise InvariantViolationException(
                "TravelerMemory must be bound to matching ConsentProfile."
            )

        self.traveler_id = traveler_id
        self.consent_profile = consent_profile
        self.profile = profile or TravelerProfile(
            traveler_id=traveler_id,
            full_name="Unregistered Traveler",
            age=30,
            gender="M",
        )
        self.preferences = preferences or PreferenceStore()
        self.journey_history = journey_history or JourneyHistory()

        self.is_purged: bool = False
        self.created_at: float = time.time()
        self.last_active_at: float = time.time()
        self._domain_events: List[DomainEvent] = []

    def _verify_consent(self) -> None:
        if self.is_purged or self.consent_profile.is_withdrawn:
            raise ConsentWithdrawnException(
                "Traveler memory access denied: consent withdrawn or purged."
            )
        if not self.consent_profile.is_granted:
            raise ConsentMissingException(
                "BR-MEM-001: Active opt-in consent is required before memory operations."
            )

    def update_profile(self, full_name: str, age: int, gender: str) -> None:
        self._verify_consent()
        self.profile = TravelerProfile(
            traveler_id=self.traveler_id,
            full_name=full_name,
            age=age,
            gender=gender,
            companions=self.profile.companions,
        )
        self.last_active_at = time.time()
        self._record_event(
            MemoryCreatedEvent(
                memory_id=str(uuid.uuid4()),
                traveler_id=self.traveler_id.value,
                category="LONG_TERM",
                details={"action": "PROFILE_UPDATED", "name": full_name, "age": age},
            )
        )

    def add_companion(self, companion: CompanionRecord) -> None:
        self._verify_consent()
        self.profile.add_companion(companion)
        self.last_active_at = time.time()

    def update_preferences(
        self,
        berth: Optional[BerthPreference] = None,
        train_class: Optional[str] = None,
        meal: Optional[str] = None,
        window: Optional[str] = None,
    ) -> None:
        self._verify_consent()
        updated_fields = {}

        if (
            berth is not None
            and berth.preference != self.preferences.berth_preference.preference
        ):
            res_berth, conflict = ConflictResolutionPolicy.resolve_preference_conflict(
                self.preferences.berth_preference, berth, "berth_preference"
            )
            if conflict:
                self._record_event(
                    PreferenceConflictDetectedEvent(
                        traveler_id=self.traveler_id.value,
                        conflicting_field="berth_preference",
                        old_value=self.preferences.berth_preference.preference.value,
                        new_value=berth.preference.value,
                    )
                )
            self.preferences.berth_preference = res_berth
            updated_fields["berth_preference"] = berth.preference.value

        if train_class and train_class.upper() != self.preferences.preferred_class:
            updated_fields["preferred_class"] = train_class.upper()
            self.preferences.preferred_class = train_class.upper()

        if meal and meal.upper() != self.preferences.meal_preference:
            updated_fields["meal_preference"] = meal.upper()
            self.preferences.meal_preference = meal.upper()

        if window and window.upper() != self.preferences.departure_window:
            updated_fields["departure_window"] = window.upper()
            self.preferences.departure_window = window.upper()

        self.preferences.updated_at = time.time()
        self.last_active_at = time.time()

        if updated_fields:
            self._record_event(
                PreferenceUpdatedEvent(
                    traveler_id=self.traveler_id.value,
                    updated_fields=updated_fields,
                )
            )

    def record_completed_trip(self, origin: str, destination: str) -> RouteFrequency:
        self._verify_consent()
        rf = self.journey_history.record_trip(origin, destination)
        self.last_active_at = time.time()
        return rf

    def purge_all_memory(self) -> int:
        """Executes Right-to-be-Forgotten purge across internal profile and preference models."""
        self.is_purged = True
        purged_count = (
            len(self.profile.companions) + len(self.journey_history.routes) + 2
        )

        # Reset state to zero knowledge
        self.profile = TravelerProfile(self.traveler_id, "Purged Traveler", 0, "U")
        self.preferences = PreferenceStore()
        self.journey_history = JourneyHistory()

        self._record_event(
            MemoryPurgedEvent(
                traveler_id=self.traveler_id.value,
                records_purged_count=purged_count,
            )
        )
        return purged_count

    def _record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    def to_dict(self) -> Dict[str, Any]:
        self._verify_consent()
        return {
            "traveler_id": self.traveler_id.value,
            "is_purged": self.is_purged,
            "profile": self.profile.to_dict(),
            "preferences": self.preferences.to_dict(),
            "journey_history": self.journey_history.to_dict(),
            "created_at": self.created_at,
            "last_active_at": self.last_active_at,
        }


class JourneySagaMemory:
    """Aggregate Root holding state for active multi-step booking workflows spanning sessions."""

    MAX_SAGA_RETENTION_SECONDS = 7 * 86400  # 7 Days max

    def __init__(
        self,
        traveler_id: TravelerId,
        origin: str,
        destination: str,
        saga_id: Optional[str] = None,
        current_step: str = "INITIATED",
        step_data: Optional[Dict[str, Any]] = None,
    ):
        if not traveler_id:
            raise InvariantViolationException(
                "JourneySagaMemory requires a valid TravelerId."
            )
        self.saga_id = saga_id or str(uuid.uuid4())
        self.traveler_id = traveler_id
        self.origin = origin.upper().strip()
        self.destination = destination.upper().strip()
        self.current_step = current_step.upper().strip()
        self.step_data: Dict[str, Any] = step_data or {}
        self.created_at: float = time.time()
        self.last_active_at: float = time.time()
        self.is_completed: bool = False
        self._domain_events: List[DomainEvent] = []

    def check_expiration(self) -> bool:
        idle_seconds = time.time() - self.last_active_at
        if idle_seconds > self.MAX_SAGA_RETENTION_SECONDS:
            raise SagaExpiredException(
                f"Saga {self.saga_id} has expired (idle > 7 days)."
            )
        return False

    def advance_step(
        self, step_name: str, data_update: Optional[Dict[str, Any]] = None
    ) -> None:
        self.check_expiration()
        self.current_step = step_name.upper().strip()
        if data_update:
            self.step_data.update(data_update)
        self.last_active_at = time.time()

    def resume_saga(self) -> Dict[str, Any]:
        self.check_expiration()
        self.last_active_at = time.time()
        self._record_event(
            JourneySagaResumedEvent(
                saga_id=self.saga_id,
                traveler_id=self.traveler_id.value,
                resumed_step=self.current_step,
            )
        )
        return {
            "saga_id": self.saga_id,
            "traveler_id": self.traveler_id.value,
            "origin": self.origin,
            "destination": self.destination,
            "current_step": self.current_step,
            "step_data": self.step_data,
            "last_active_at": self.last_active_at,
        }

    def complete_saga(self) -> None:
        self.is_completed = True
        self.current_step = "COMPLETED"
        self.last_active_at = time.time()

    def _record_event(self, event: DomainEvent) -> None:
        self._domain_events.append(event)

    def pop_domain_events(self) -> List[DomainEvent]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events
