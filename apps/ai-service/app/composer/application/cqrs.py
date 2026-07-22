"""
CQRS Catalog for Milestone 6.6 AI Response Composer Platform.
Explicit segregation of write operations (Commands) and read operations (Queries) with dedicated handlers.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional

from app.composer.domain.services import (
    ArbitrationDomainService,
    ExplainabilityService,
)
from app.composer.domain.repositories import (
    IResponseCompositionRepository,
    IConversationSessionRepository,
    IComposerAuditLogger,
    IUpstreamIntelligencePort,
)
from app.composer.pipeline.stages import CompositionPipeline


# =====================================================================
# CQRS COMMANDS (WRITE SIDE)
# =====================================================================


@dataclass(frozen=True)
class ComposeResponseCommand:
    """Command triggering multi-source response composition."""

    traveler_id: str
    session_id: str
    prompt: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    train_number: Optional[str] = None


@dataclass(frozen=True)
class ArbitrateConflictCommand:
    """Command resolving contradictory upstream model predictions."""

    planner_option: Dict[str, Any]
    prediction_option: Dict[str, Any]
    memory_preference: Dict[str, Any]
    operational_status: Dict[str, Any]


@dataclass(frozen=True)
class AttachExplanationCommand:
    """Command generating multi-tiered explainability payload."""

    prediction_data: Dict[str, Any]
    policy_data: Dict[str, Any]
    confidence_score: float
    persona: str = "NORMAL"


# =====================================================================
# CQRS QUERIES (READ SIDE)
# =====================================================================


@dataclass(frozen=True)
class GetComposedResponseQuery:
    """Query fetching formatted response for active session."""

    composition_id: str


@dataclass(frozen=True)
class GetExplanationDetailQuery:
    """Query retrieving deep Level 3/4 evidence audit."""

    explanation_id: str


@dataclass(frozen=True)
class GetResponseAuditTrailQuery:
    """Query retrieving immutable audit history for traveler."""

    traveler_id: str


# =====================================================================
# CQRS COMMAND HANDLERS
# =====================================================================


class ComposeResponseCommandHandler:
    """Handler executing ComposeResponseCommand via pipeline execution."""

    def __init__(
        self,
        composition_repo: IResponseCompositionRepository,
        session_repo: IConversationSessionRepository,
        audit_logger: IComposerAuditLogger,
        upstream_port: IUpstreamIntelligencePort,
    ):
        self.composition_repo = composition_repo
        self.session_repo = session_repo
        self.audit_logger = audit_logger
        self.upstream_port = upstream_port
        self.pipeline = CompositionPipeline()

    def handle(self, cmd: ComposeResponseCommand) -> Dict[str, Any]:
        pipeline_ctx = self.pipeline.execute(
            traveler_id=cmd.traveler_id,
            session_id=cmd.session_id,
            prompt=cmd.prompt,
        )

        if pipeline_ctx.composition:
            self.composition_repo.save(pipeline_ctx.composition)

            self.audit_logger.log_event(
                event_type="RESPONSE_COMPOSED",
                session_id=cmd.session_id,
                traveler_id=cmd.traveler_id,
                details={
                    "composition_id": pipeline_ctx.composition.composition_id,
                    "latency_ms": pipeline_ctx.latency_ms,
                },
            )

            return {
                "status": "SUCCESS",
                "composition_id": pipeline_ctx.composition.composition_id,
                "response": pipeline_ctx.composition.to_dict(),
                "latency_ms": pipeline_ctx.latency_ms,
            }

        return {"status": "FAILED", "reason": "Composition pipeline returned empty result"}


class ArbitrateConflictCommandHandler:
    """Handler executing ArbitrateConflictCommand."""

    def handle(self, cmd: ArbitrateConflictCommand) -> Dict[str, Any]:
        arbitration = ArbitrationDomainService.arbitrate(
            planner_option=cmd.planner_option,
            prediction_option=cmd.prediction_option,
            memory_preference=cmd.memory_preference,
            operational_status=cmd.operational_status,
        )
        return {"status": "SUCCESS", "arbitration": arbitration.to_dict()}


class AttachExplanationCommandHandler:
    """Handler executing AttachExplanationCommand."""

    def handle(self, cmd: AttachExplanationCommand) -> Dict[str, Any]:
        payload = ExplainabilityService.generate_explanation(
            prediction_data=cmd.prediction_data,
            policy_data=cmd.policy_data,
            confidence_score=cmd.confidence_score,
            persona=cmd.persona,
        )
        return {"status": "SUCCESS", "explanation": payload.to_dict()}


# =====================================================================
# CQRS QUERY HANDLERS
# =====================================================================


class GetComposedResponseQueryHandler:
    """Handler executing GetComposedResponseQuery."""

    def __init__(self, composition_repo: IResponseCompositionRepository):
        self.composition_repo = composition_repo

    def handle(self, query: GetComposedResponseQuery) -> Dict[str, Any]:
        comp = self.composition_repo.get_by_id(query.composition_id)
        if not comp:
            return {"found": False, "composition": None}
        return {"found": True, "composition": comp.to_dict()}


class GetResponseAuditTrailQueryHandler:
    """Handler executing GetResponseAuditTrailQuery."""

    def __init__(self, audit_logger: IComposerAuditLogger):
        self.audit_logger = audit_logger

    def handle(self, query: GetResponseAuditTrailQuery) -> Dict[str, Any]:
        trail = self.audit_logger.get_audit_trail(query.traveler_id)
        return {"traveler_id": query.traveler_id, "audit_count": len(trail), "trail": trail}
