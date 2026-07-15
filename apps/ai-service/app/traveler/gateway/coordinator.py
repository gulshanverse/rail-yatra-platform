# app/traveler/gateway/coordinator.py
import time
import uuid
from typing import Dict, Any, List, Optional
from app.traveler.interfaces.contracts import (
    ITravelerGateway,
    ITravelerCoordinator,
    IPipelineOrchestrator,
    IAuditEngine,
    IMetricsEngine,
    IEventPublisher,
)
from app.traveler.dto.models import (
    TravelerGuidanceDTO,
    TravelerEventDTO,
    TravelerAuditDTO,
)


class TravelerDecisionContext:
    def __init__(
        self,
        correlation_id: str,
        telemetry: Dict[str, Any],
        traveler_id: str,
        journey_id: str,
        booking_id: str,
        timeline_version: str = "T_V1",
        decision_version: str = "D_1.0.0",
        active_state: str = "PRE_DEPARTURE",
        status: str = "PUNCTUAL",
        events: Optional[List[TravelerEventDTO]] = None,
        alerts: Optional[List[Any]] = None,
        reminders: Optional[List[Any]] = None,
        recommended_action: Optional[Any] = None,
        explanation: Optional[Any] = None,
        confidence_score: float = 1.0,
        recovery_plan: Optional[Any] = None,
    ):
        self.correlation_id = correlation_id
        self.telemetry = telemetry
        self.traveler_id = traveler_id
        self.journey_id = journey_id
        self.booking_id = booking_id
        self.timeline_version = timeline_version
        self.decision_version = decision_version
        self.active_state = active_state
        self.status = status
        self.events = events or []
        self.alerts = alerts or []
        self.reminders = reminders or []
        self.recommended_action = recommended_action
        self.explanation = explanation
        self.confidence_score = confidence_score
        self.recovery_plan = recovery_plan

    def copy_with(self, **kwargs) -> "TravelerDecisionContext":
        return TravelerDecisionContext(
            correlation_id=kwargs.get("correlation_id", self.correlation_id),
            telemetry=kwargs.get("telemetry", self.telemetry),
            traveler_id=kwargs.get("traveler_id", self.traveler_id),
            journey_id=kwargs.get("journey_id", self.journey_id),
            booking_id=kwargs.get("booking_id", self.booking_id),
            timeline_version=kwargs.get("timeline_version", self.timeline_version),
            decision_version=kwargs.get("decision_version", self.decision_version),
            active_state=kwargs.get("active_state", self.active_state),
            status=kwargs.get("status", self.status),
            events=kwargs.get("events", self.events),
            alerts=kwargs.get("alerts", self.alerts),
            reminders=kwargs.get("reminders", self.reminders),
            recommended_action=kwargs.get(
                "recommended_action", self.recommended_action
            ),
            explanation=kwargs.get("explanation", self.explanation),
            confidence_score=kwargs.get("confidence_score", self.confidence_score),
            recovery_plan=kwargs.get("recovery_plan", self.recovery_plan),
        )


class TravelerDecisionContextFactory:
    @staticmethod
    def create_context(
        telemetry: Dict[str, Any], correlation_id: str
    ) -> TravelerDecisionContext:
        traveler_id = telemetry.get("traveler_id")
        journey_id = telemetry.get("journey_id")
        booking_id = telemetry.get("booking_id")

        if not traveler_id:
            raise ValueError("Traveler ID is required in telemetry.")
        if not journey_id:
            raise ValueError("Journey ID is required in telemetry.")
        if not booking_id:
            raise ValueError("Booking ID is required in telemetry.")
        if not correlation_id:
            raise ValueError("Correlation ID is required.")

        return TravelerDecisionContext(
            correlation_id=correlation_id,
            telemetry=telemetry,
            traveler_id=traveler_id,
            journey_id=journey_id,
            booking_id=booking_id,
        )


class TravelerCoordinator(ITravelerCoordinator):
    def __init__(
        self,
        orchestrator: IPipelineOrchestrator,
        audit_engine: IAuditEngine,
        metrics_engine: IMetricsEngine,
        event_publisher: IEventPublisher,
    ):
        self.orchestrator = orchestrator
        self.audit_engine = audit_engine
        self.metrics_engine = metrics_engine
        self.event_publisher = event_publisher

    async def coordinate_assistance(
        self, context: TravelerDecisionContext
    ) -> TravelerGuidanceDTO:
        start_time = time.time()

        # Run sequential calculation orchestrator pipeline
        final_context = await self.orchestrator.execute_pipeline(context)

        # Build guidance DTO
        from app.traveler.dto.models import TravelerActionDTO, TravelerExplanationDTO

        action_dto = None
        if final_context.recommended_action:
            action_dto = TravelerActionDTO(
                action_code=final_context.recommended_action.get("action_code", "WAIT"),
                description=final_context.recommended_action.get(
                    "description", "No immediate actions required."
                ),
                urgency=final_context.recommended_action.get("urgency", "LOW"),
            )

        explanation_dto = None
        if final_context.explanation:
            explanation_dto = TravelerExplanationDTO(
                reason_code=final_context.explanation.get("reason_code", "E_PUNCTUAL"),
                text=final_context.explanation.get(
                    "text", "Journey continues on schedule."
                ),
                supporting_evidence=final_context.explanation.get(
                    "supporting_evidence", {}
                ),
            )

        guidance_dto = TravelerGuidanceDTO(
            guidance_id=f"guid_{uuid.uuid4().hex[:8]}",
            correlation_id=context.correlation_id,
            timestamp=time.time(),
            traveler_id=context.traveler_id,
            active_state=final_context.active_state,
            status=final_context.status,
            recommended_action=action_dto,
            explanation=explanation_dto,
            confidence_score=final_context.confidence_score,
        )

        # Audit decision log
        audit_rec = TravelerAuditDTO(
            audit_record_id=f"aud_trv_{uuid.uuid4().hex[:8]}",
            guidance_id=guidance_dto.guidance_id,
            traveler_id=guidance_dto.traveler_id,
            journey_id=context.journey_id,
            booking_id=context.booking_id,
            timeline_version=final_context.timeline_version,
            decision_version=final_context.decision_version,
            correlation_id=context.correlation_id,
            reason_code=explanation_dto.reason_code
            if explanation_dto
            else "E_PUNCTUAL",
            supporting_evidence=explanation_dto.supporting_evidence
            if explanation_dto
            else {},
            confidence=guidance_dto.confidence_score,
            selected_action=action_dto.action_code if action_dto else "WAIT",
            outcome_status="DELIVERED",
            retention_policy="7_YEARS",
        )
        await self.audit_engine.log_guidance(audit_rec)

        # Publish domain events
        await self.event_publisher.publish_event(
            "TravelerGuidanceGenerated",
            {
                "guidance_id": guidance_dto.guidance_id,
                "correlation_id": context.correlation_id,
                "timestamp": guidance_dto.timestamp,
            },
        )

        duration_ms = (time.time() - start_time) * 1000
        self.metrics_engine.increment_metric(
            "traveler_pipeline_latency_ms", duration_ms
        )

        return guidance_dto


class TravelerAssistanceGateway(ITravelerGateway):
    def __init__(self, coordinator: ITravelerCoordinator):
        self.coordinator = coordinator

    async def process_telemetry_update(
        self, telemetry: Dict[str, Any], correlation_id: str
    ) -> TravelerGuidanceDTO:
        # Build decision context
        context = TravelerDecisionContextFactory.create_context(
            telemetry, correlation_id
        )
        return await self.coordinator.coordinate_assistance(context)
