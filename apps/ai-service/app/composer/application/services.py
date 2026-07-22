"""
Application Orchestration Services for Milestone 6.6 AI Response Composer Platform.
Coordinates domain aggregates, use cases, and CQRS handlers under Clean Architecture.
"""

from typing import Dict, Any, Optional

from app.composer.application.cqrs import (
    ComposeResponseCommand,
    ComposeResponseCommandHandler,
    ArbitrateConflictCommand,
    ArbitrateConflictCommandHandler,
    AttachExplanationCommand,
    AttachExplanationCommandHandler,
    GetComposedResponseQuery,
    GetComposedResponseQueryHandler,
    GetResponseAuditTrailQuery,
    GetResponseAuditTrailQueryHandler,
)
from app.composer.domain.repositories import (
    IResponseCompositionRepository,
    IConversationSessionRepository,
    IComposerAuditLogger,
    IUpstreamIntelligencePort,
)
from app.composer.infrastructure.repositories import (
    InMemoryResponseCompositionRepository,
    InMemoryConversationSessionRepository,
    InMemoryComposerAuditLogger,
)
from app.composer.infrastructure.adapters import InMemoryUpstreamIntelligenceAdapter


class ResponseApplicationService:
    """Application Service orchestrating UC-RSP-01 (Compose Journey Plan Response) & UC-RSP-03 (Operational Disruption)."""

    def __init__(
        self,
        composition_repo: Optional[IResponseCompositionRepository] = None,
        session_repo: Optional[IConversationSessionRepository] = None,
        audit_logger: Optional[IComposerAuditLogger] = None,
        upstream_port: Optional[IUpstreamIntelligencePort] = None,
    ):
        self.composition_repo = composition_repo or InMemoryResponseCompositionRepository()
        self.session_repo = session_repo or InMemoryConversationSessionRepository()
        self.audit_logger = audit_logger or InMemoryComposerAuditLogger()
        self.upstream_port = upstream_port or InMemoryUpstreamIntelligenceAdapter()

        self.compose_handler = ComposeResponseCommandHandler(
            self.composition_repo,
            self.session_repo,
            self.audit_logger,
            self.upstream_port,
        )
        self.get_response_handler = GetComposedResponseQueryHandler(self.composition_repo)

    def compose_journey_response(
        self,
        traveler_id: str,
        session_id: str,
        prompt: str,
        origin: Optional[str] = None,
        destination: Optional[str] = None,
    ) -> Dict[str, Any]:
        """UC-RSP-01: Compose scannable journey plan response."""
        cmd = ComposeResponseCommand(
            traveler_id=traveler_id,
            session_id=session_id,
            prompt=prompt,
            origin=origin,
            destination=destination,
        )
        return self.compose_handler.handle(cmd)

    def get_composed_response(self, composition_id: str) -> Dict[str, Any]:
        """Retrieves composed response by ID."""
        query = GetComposedResponseQuery(composition_id=composition_id)
        return self.get_response_handler.handle(query)


class ExplainabilityApplicationService:
    """Application Service orchestrating UC-RSP-02 (Explain Prediction Odds)."""

    def __init__(self):
        self.explain_handler = AttachExplanationCommandHandler()
        self.arbitrate_handler = ArbitrateConflictCommandHandler()

    def explain_prediction_odds(
        self,
        prediction_data: Dict[str, Any],
        policy_data: Dict[str, Any],
        confidence_score: float,
        persona: str = "NORMAL",
    ) -> Dict[str, Any]:
        """UC-RSP-02: Generates multi-tiered explainability payload for waitlist predictions."""
        cmd = AttachExplanationCommand(
            prediction_data=prediction_data,
            policy_data=policy_data,
            confidence_score=confidence_score,
            persona=persona,
        )
        return self.explain_handler.handle(cmd)

    def arbitrate_subsystem_conflict(
        self,
        planner_option: Dict[str, Any],
        prediction_option: Dict[str, Any],
        memory_preference: Dict[str, Any],
        operational_status: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Resolves conflicting advice between Planner and Prediction models."""
        cmd = ArbitrateConflictCommand(
            planner_option=planner_option,
            prediction_option=prediction_option,
            memory_preference=memory_preference,
            operational_status=operational_status,
        )
        return self.arbitrate_handler.handle(cmd)


class ConversationOrchestrationService:
    """Application Service orchestrating UC-RSP-04 (Recover Interrupted Saga) and multi-turn context."""

    def __init__(
        self,
        session_repo: Optional[IConversationSessionRepository] = None,
    ):
        self.session_repo = session_repo or InMemoryConversationSessionRepository()

    def get_session_context(self, traveler_id: str) -> Dict[str, Any]:
        """UC-RSP-04: Queries active conversation session for saga resumption."""
        session = self.session_repo.get_active_session_by_traveler(traveler_id)
        if not session:
            return {"has_active_session": False, "session": None}
        return {"has_active_session": True, "session": session.to_dict()}


class ResponseGovernanceApplicationService:
    """Application Service managing DPDP privacy checks and audit trail queries."""

    def __init__(
        self,
        audit_logger: Optional[IComposerAuditLogger] = None,
    ):
        self.audit_logger = audit_logger or InMemoryComposerAuditLogger()
        self.audit_query_handler = GetResponseAuditTrailQueryHandler(self.audit_logger)

    def get_response_audit_trail(self, traveler_id: str) -> Dict[str, Any]:
        """Retrieves immutable composition audit trail for traveler."""
        query = GetResponseAuditTrailQuery(traveler_id=traveler_id)
        return self.audit_query_handler.handle(query)
