"""
Application Orchestration Services for Milestone 6.5 AI Memory Platform.
Coordinates domain aggregates, use cases, and CQRS handlers under Clean Architecture.
"""

from typing import Dict, Any, Optional

from app.memory.domain.value_objects import TravelerId
from app.memory.domain.repositories import (
    ITravelerMemoryRepository,
    IConsentProfileRepository,
    IJourneySagaRepository,
    IMemoryAuditLogger,
    InMemoryTravelerMemoryRepository,
    InMemoryConsentProfileRepository,
    InMemoryJourneySagaRepository,
    InMemoryAuditLogger,
)
from app.memory.domain.services import MemoryQualityService
from app.memory.application.cqrs import (
    GrantConsentCommand,
    GrantConsentCommandHandler,
    WithdrawConsentCommand,
    WithdrawConsentCommandHandler,
    CreateMemoryCommand,
    CreateMemoryCommandHandler,
    UpdatePreferenceCommand,
    UpdatePreferenceCommandHandler,
    ResumeSagaCommand,
    ResumeSagaCommandHandler,
    GetTravelerMemoryQuery,
    GetTravelerMemoryQueryHandler,
    GetConsentStatusQuery,
    GetConsentStatusQueryHandler,
    GetRecentContextQuery,
    GetRecentContextQueryHandler,
    GetMemoryAuditQuery,
    GetMemoryAuditQueryHandler,
)


class ConsentApplicationService:
    """Application Service managing consent opt-in, verification, and right-to-be-forgotten purges."""

    def __init__(
        self,
        consent_repo: Optional[IConsentProfileRepository] = None,
        memory_repo: Optional[ITravelerMemoryRepository] = None,
        audit_logger: Optional[IMemoryAuditLogger] = None,
    ):
        self.consent_repo = consent_repo or InMemoryConsentProfileRepository()
        self.audit_logger = audit_logger or InMemoryAuditLogger()
        self.memory_repo = memory_repo or InMemoryTravelerMemoryRepository(
            consent_repo=self.consent_repo
        )

        self.grant_handler = GrantConsentCommandHandler(
            self.consent_repo, self.audit_logger
        )
        self.withdraw_handler = WithdrawConsentCommandHandler(
            self.memory_repo, self.consent_repo, self.audit_logger
        )
        self.status_query_handler = GetConsentStatusQueryHandler(self.consent_repo)

    def grant_consent(
        self, traveler_id: str, scope: str = "FULL_MEMORY_PERSONALIZATION"
    ) -> Dict[str, Any]:
        cmd = GrantConsentCommand(traveler_id=traveler_id, scope=scope)
        return self.grant_handler.handle(cmd)

    def withdraw_consent(
        self, traveler_id: str, reason: str = "USER_REQUEST"
    ) -> Dict[str, Any]:
        cmd = WithdrawConsentCommand(traveler_id=traveler_id, reason=reason)
        return self.withdraw_handler.handle(cmd)

    def get_consent_status(self, traveler_id: str) -> Dict[str, Any]:
        query = GetConsentStatusQuery(traveler_id=traveler_id)
        return self.status_query_handler.handle(query)


class MemoryApplicationService:
    """Application Service orchestrating UC-MEM-01 (Store Profile) and UC-MEM-02 (Auto-Fill Parameters)."""

    def __init__(
        self,
        memory_repo: Optional[ITravelerMemoryRepository] = None,
        consent_repo: Optional[IConsentProfileRepository] = None,
        audit_logger: Optional[IMemoryAuditLogger] = None,
    ):
        self.consent_repo = consent_repo or InMemoryConsentProfileRepository()
        self.memory_repo = memory_repo or InMemoryTravelerMemoryRepository(
            consent_repo=self.consent_repo
        )
        self.audit_logger = audit_logger or InMemoryAuditLogger()

        self.create_memory_handler = CreateMemoryCommandHandler(
            self.memory_repo, self.consent_repo, self.audit_logger
        )
        self.update_pref_handler = UpdatePreferenceCommandHandler(
            self.memory_repo, self.consent_repo, self.audit_logger
        )
        self.get_memory_query_handler = GetTravelerMemoryQueryHandler(
            self.memory_repo, self.consent_repo
        )

    def store_traveler_profile(
        self,
        traveler_id: str,
        full_name: str,
        age: int,
        gender: str,
        companion_name: Optional[str] = None,
        companion_age: Optional[int] = None,
        companion_gender: Optional[str] = None,
    ) -> Dict[str, Any]:
        """UC-MEM-01: Store passenger profile details."""
        cmd = CreateMemoryCommand(
            traveler_id=traveler_id,
            full_name=full_name,
            age=age,
            gender=gender,
            companion_name=companion_name,
            companion_age=companion_age,
            companion_gender=companion_gender,
        )
        return self.create_memory_handler.handle(cmd)

    def update_preferences(
        self,
        traveler_id: str,
        berth_preference: Optional[str] = None,
        preferred_class: Optional[str] = None,
        meal_preference: Optional[str] = None,
        departure_window: Optional[str] = None,
        meal: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update traveler preferences."""
        effective_meal = meal_preference or meal
        cmd = UpdatePreferenceCommand(
            traveler_id=traveler_id,
            berth_preference=berth_preference,
            preferred_class=preferred_class,
            meal_preference=effective_meal,
            departure_window=departure_window,
        )
        return self.update_pref_handler.handle(cmd)

    def auto_fill_booking_parameters(self, traveler_id: str) -> Dict[str, Any]:
        """UC-MEM-02: Retrieve consent-filtered preferences and passenger manifests for auto-fill."""
        query = GetTravelerMemoryQuery(traveler_id=traveler_id)
        return self.get_memory_query_handler.handle(query)


class JourneySagaApplicationService:
    """Application Service orchestrating UC-MEM-03 (Resume Interrupted Booking Saga)."""

    def __init__(
        self,
        saga_repo: Optional[IJourneySagaRepository] = None,
        audit_logger: Optional[IMemoryAuditLogger] = None,
    ):
        self.saga_repo = saga_repo or InMemoryJourneySagaRepository()
        self.audit_logger = audit_logger or InMemoryAuditLogger()

        self.resume_handler = ResumeSagaCommandHandler(
            self.saga_repo, self.audit_logger
        )
        self.recent_context_handler = GetRecentContextQueryHandler(self.saga_repo)

    def get_recent_context(self, traveler_id: str) -> Dict[str, Any]:
        """Queries active saga context for workflow resumption."""
        query = GetRecentContextQuery(traveler_id=traveler_id)
        return self.recent_context_handler.handle(query)

    def resume_booking_saga(self, saga_id: str, traveler_id: str) -> Dict[str, Any]:
        """UC-MEM-03: Resumes pending booking saga workflow state."""
        cmd = ResumeSagaCommand(saga_id=saga_id, traveler_id=traveler_id)
        return self.resume_handler.handle(cmd)


class MemoryGovernanceApplicationService:
    """Application Service providing audit history and quality metrics computation."""

    def __init__(
        self,
        memory_repo: Optional[ITravelerMemoryRepository] = None,
        audit_logger: Optional[IMemoryAuditLogger] = None,
    ):
        self.memory_repo = memory_repo or InMemoryTravelerMemoryRepository()
        self.audit_logger = audit_logger or InMemoryAuditLogger()
        self.audit_query_handler = GetMemoryAuditQueryHandler(self.audit_logger)

    def get_memory_audit_trail(self, traveler_id: str) -> Dict[str, Any]:
        """Retrieves immutable audit history for user inspection."""
        query = GetMemoryAuditQuery(traveler_id=traveler_id)
        return self.audit_query_handler.handle(query)

    def get_memory_quality(self, traveler_id: str) -> Dict[str, Any]:
        """Computes freshness, completeness, and quality metrics."""
        t_id = TravelerId(traveler_id)
        memory = self.memory_repo.get_by_traveler_id(t_id)
        if not memory:
            return {
                "traveler_id": traveler_id,
                "freshness_score": 0.0,
                "completeness_score": 0.0,
                "overall_quality_score": 0.0,
            }
        quality = MemoryQualityService.calculate_memory_quality(memory)
        quality["traveler_id"] = traveler_id
        return quality
