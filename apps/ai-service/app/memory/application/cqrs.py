"""
CQRS Command & Query Models and Handlers for Milestone 6.5 AI Memory Platform.
Strictly separates state mutations (Commands) from read projections (Queries).
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from app.memory.domain.value_objects import (
    TravelerId,
    BerthPreference,
    BerthPreferenceEnum,
    ConsentStatusEnum,
)
from app.memory.domain.aggregates import TravelerMemory, ConsentProfile
from app.memory.domain.entities import CompanionRecord, MemoryAuditEntry
from app.memory.domain.repositories import (
    ITravelerMemoryRepository,
    IConsentProfileRepository,
    IJourneySagaRepository,
    IMemoryAuditLogger,
)
from app.memory.domain.services import ConsentEvaluationService, MemoryPurgeService
from app.memory.exceptions import (
    InvariantViolationException,
)

# =====================================================================
# Commands (Mutations)
# =====================================================================


@dataclass(frozen=True)
class CreateMemoryCommand:
    traveler_id: str
    full_name: str
    age: int
    gender: str
    companion_name: Optional[str] = None
    companion_age: Optional[int] = None
    companion_gender: Optional[str] = None


@dataclass(frozen=True)
class UpdatePreferenceCommand:
    traveler_id: str
    berth_preference: Optional[str] = None
    preferred_class: Optional[str] = None
    meal_preference: Optional[str] = None
    departure_window: Optional[str] = None


@dataclass(frozen=True)
class GrantConsentCommand:
    traveler_id: str
    scope: str = "FULL_MEMORY_PERSONALIZATION"


@dataclass(frozen=True)
class WithdrawConsentCommand:
    traveler_id: str
    reason: str = "USER_REQUEST"


@dataclass(frozen=True)
class ResumeSagaCommand:
    saga_id: str
    traveler_id: str


# =====================================================================
# Queries (Read Projections)
# =====================================================================


@dataclass(frozen=True)
class GetTravelerMemoryQuery:
    traveler_id: str


@dataclass(frozen=True)
class GetRecentContextQuery:
    traveler_id: str


@dataclass(frozen=True)
class GetConsentStatusQuery:
    traveler_id: str


@dataclass(frozen=True)
class GetMemoryAuditQuery:
    traveler_id: str


# =====================================================================
# Command Handlers
# =====================================================================


class GrantConsentCommandHandler:
    """Handler for granting user memory consent."""

    def __init__(
        self,
        consent_repo: IConsentProfileRepository,
        audit_logger: IMemoryAuditLogger,
    ):
        self.consent_repo = consent_repo
        self.audit_logger = audit_logger

    def handle(self, command: GrantConsentCommand) -> Dict[str, Any]:
        t_id = TravelerId(command.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)
        if not consent:
            consent = ConsentProfile(traveler_id=t_id)

        consent.grant_consent(scope=command.scope)
        self.consent_repo.save(consent)

        audit_entry = MemoryAuditEntry(
            traveler_id=command.traveler_id,
            action="GRANT_CONSENT",
            actor="USER",
            details={"scope": command.scope},
        )
        self.audit_logger.log_entry(audit_entry)

        return {
            "status": "SUCCESS",
            "consent_status": consent.consent_status.status.value,
        }


class WithdrawConsentCommandHandler:
    """Handler executing Right-to-be-Forgotten consent withdrawal and purge."""

    def __init__(
        self,
        memory_repo: ITravelerMemoryRepository,
        consent_repo: IConsentProfileRepository,
        audit_logger: IMemoryAuditLogger,
    ):
        self.memory_repo = memory_repo
        self.consent_repo = consent_repo
        self.audit_logger = audit_logger

    def handle(self, command: WithdrawConsentCommand) -> Dict[str, Any]:
        t_id = TravelerId(command.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)
        if not consent:
            consent = ConsentProfile(traveler_id=t_id)

        memory = self.memory_repo.get_by_traveler_id(t_id)
        records_purged = 0

        if memory:
            records_purged = MemoryPurgeService.execute_purge(
                memory_aggregate=memory,
                consent_profile=consent,
                reason=command.reason,
            )
            self.memory_repo.save(memory)
        else:
            consent.withdraw_consent(reason=command.reason)

        self.consent_repo.save(consent)

        audit_entry = MemoryAuditEntry(
            traveler_id=command.traveler_id,
            action="WITHDRAW_CONSENT_PURGE",
            actor="USER",
            details={"reason": command.reason, "records_purged": records_purged},
        )
        self.audit_logger.log_entry(audit_entry)

        return {"status": "SUCCESS", "records_purged": records_purged}


class CreateMemoryCommandHandler:
    """Handler for recording traveler profile and companion details."""

    def __init__(
        self,
        memory_repo: ITravelerMemoryRepository,
        consent_repo: IConsentProfileRepository,
        audit_logger: IMemoryAuditLogger,
    ):
        self.memory_repo = memory_repo
        self.consent_repo = consent_repo
        self.audit_logger = audit_logger
        self.consent_eval = ConsentEvaluationService()

    def handle(self, command: CreateMemoryCommand) -> Dict[str, Any]:
        t_id = TravelerId(command.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)
        self.consent_eval.verify_consent(consent)
        assert consent is not None

        memory = self.memory_repo.get_by_traveler_id(t_id)
        if not memory:
            memory = TravelerMemory(traveler_id=t_id, consent_profile=consent)

        memory.update_profile(
            full_name=command.full_name,
            age=command.age,
            gender=command.gender,
        )

        if command.companion_name and command.companion_age:
            comp = CompanionRecord(
                name=command.companion_name,
                age=command.companion_age,
                gender=command.companion_gender or "M",
            )
            memory.add_companion(comp)

        self.memory_repo.save(memory)

        audit_entry = MemoryAuditEntry(
            traveler_id=command.traveler_id,
            action="CREATE_MEMORY_PROFILE",
            actor="ASSISTANT",
            details={"profile": memory.profile.to_dict()},
        )
        self.audit_logger.log_entry(audit_entry)

        return {"status": "SUCCESS", "memory": memory.to_dict()}


class UpdatePreferenceCommandHandler:
    """Handler for updating traveler seating, meal, or train class preferences."""

    def __init__(
        self,
        memory_repo: ITravelerMemoryRepository,
        consent_repo: IConsentProfileRepository,
        audit_logger: IMemoryAuditLogger,
    ):
        self.memory_repo = memory_repo
        self.consent_repo = consent_repo
        self.audit_logger = audit_logger
        self.consent_eval = ConsentEvaluationService()

    def handle(self, command: UpdatePreferenceCommand) -> Dict[str, Any]:
        t_id = TravelerId(command.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)
        self.consent_eval.verify_consent(consent)
        assert consent is not None

        memory = self.memory_repo.get_by_traveler_id(t_id)
        if not memory:
            memory = TravelerMemory(traveler_id=t_id, consent_profile=consent)

        berth_obj = None
        if command.berth_preference:
            pref_enum = BerthPreferenceEnum[command.berth_preference.upper()]
            berth_obj = BerthPreference(preference=pref_enum)

        memory.update_preferences(
            berth=berth_obj,
            train_class=command.preferred_class,
            meal=command.meal_preference,
            window=command.departure_window,
        )

        self.memory_repo.save(memory)

        audit_entry = MemoryAuditEntry(
            traveler_id=command.traveler_id,
            action="UPDATE_PREFERENCES",
            actor="USER",
            details={"preferences": memory.preferences.to_dict()},
        )
        self.audit_logger.log_entry(audit_entry)

        return {"status": "SUCCESS", "preferences": memory.preferences.to_dict()}


class ResumeSagaCommandHandler:
    """Handler for reloading an interrupted multi-session booking saga."""

    def __init__(
        self,
        saga_repo: IJourneySagaRepository,
        audit_logger: IMemoryAuditLogger,
    ):
        self.saga_repo = saga_repo
        self.audit_logger = audit_logger

    def handle(self, command: ResumeSagaCommand) -> Dict[str, Any]:
        saga = self.saga_repo.get_by_saga_id(command.saga_id)
        if not saga:
            raise InvariantViolationException(f"Saga {command.saga_id} not found.")

        resumed_data = saga.resume_saga()
        self.saga_repo.save(saga)

        audit_entry = MemoryAuditEntry(
            traveler_id=command.traveler_id,
            action="RESUME_SAGA",
            actor="USER",
            details={"saga_id": command.saga_id, "step": saga.current_step},
        )
        self.audit_logger.log_entry(audit_entry)

        return {"status": "SUCCESS", "saga": resumed_data}


# =====================================================================
# Query Handlers (Read Projections)
# =====================================================================


class GetTravelerMemoryQueryHandler:
    """Query Handler returning consent-filtered traveler preferences and profiles."""

    def __init__(
        self,
        memory_repo: ITravelerMemoryRepository,
        consent_repo: IConsentProfileRepository,
    ):
        self.memory_repo = memory_repo
        self.consent_repo = consent_repo
        self.consent_eval = ConsentEvaluationService()

    def handle(self, query: GetTravelerMemoryQuery) -> Dict[str, Any]:
        t_id = TravelerId(query.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)

        # Enforce Consent Policy: if unconsented, return zero-knowledge payload
        if not consent or not consent.is_granted:
            return {
                "traveler_id": query.traveler_id,
                "has_consent": False,
                "profile": None,
                "preferences": None,
                "journey_history": None,
            }

        memory = self.memory_repo.get_by_traveler_id(t_id)
        if not memory or memory.is_purged:
            return {
                "traveler_id": query.traveler_id,
                "has_consent": True,
                "profile": None,
                "preferences": None,
                "journey_history": None,
            }

        return {
            "traveler_id": query.traveler_id,
            "has_consent": True,
            "profile": memory.profile.to_dict(),
            "preferences": memory.preferences.to_dict(),
            "journey_history": memory.journey_history.to_dict(),
        }


class GetConsentStatusQueryHandler:
    """Query Handler returning active consent flags for a traveler."""

    def __init__(self, consent_repo: IConsentProfileRepository):
        self.consent_repo = consent_repo

    def handle(self, query: GetConsentStatusQuery) -> Dict[str, Any]:
        t_id = TravelerId(query.traveler_id)
        consent = self.consent_repo.get_by_traveler_id(t_id)
        if not consent:
            return {
                "traveler_id": query.traveler_id,
                "status": ConsentStatusEnum.PENDING_VERIFICATION.value,
                "is_active": False,
            }
        return {
            "traveler_id": query.traveler_id,
            "status": consent.consent_status.status.value,
            "is_active": consent.is_granted,
            "scope": consent.consent_status.consent_scope,
        }


class GetRecentContextQueryHandler:
    """Query Handler returning active booking saga context for workflow resumption."""

    def __init__(self, saga_repo: IJourneySagaRepository):
        self.saga_repo = saga_repo

    def handle(self, query: GetRecentContextQuery) -> Dict[str, Any]:
        t_id = TravelerId(query.traveler_id)
        active_saga = self.saga_repo.get_active_saga_by_traveler_id(t_id)
        if not active_saga:
            return {
                "traveler_id": query.traveler_id,
                "has_active_saga": False,
                "saga": None,
            }

        return {
            "traveler_id": query.traveler_id,
            "has_active_saga": True,
            "saga": {
                "saga_id": active_saga.saga_id,
                "origin": active_saga.origin,
                "destination": active_saga.destination,
                "current_step": active_saga.current_step,
                "step_data": active_saga.step_data,
                "last_active_at": active_saga.last_active_at,
            },
        }


class GetMemoryAuditQueryHandler:
    """Query Handler returning immutable governance audit trails."""

    def __init__(self, audit_logger: IMemoryAuditLogger):
        self.audit_logger = audit_logger

    def handle(self, query: GetMemoryAuditQuery) -> Dict[str, Any]:
        entries = self.audit_logger.get_audit_trail(query.traveler_id)
        return {
            "traveler_id": query.traveler_id,
            "audit_count": len(entries),
            "trail": [e.to_dict() for e in entries],
        }
