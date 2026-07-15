# app/booking/gateway/coordinator.py
import time
import uuid
from typing import List, Dict, Any, Optional
from app.booking.interfaces.contracts import (
    IBookingGateway,
    IBookingCoordinator,
    IBookingCandidateBuilder,
    IAvailabilityEngine,
    IConfirmationEngine,
    IQuotaEngine,
    IBoardingEngine,
    IConstraintEngine,
    IRiskEngine,
    IScoringEngine,
    IRankingEngine,
    IConflictResolutionEngine,
    IRecommendationEngine,
    IExplanationEngine,
    IAuditEngine,
    IMetricsEngine,
    IEventPublisher,
)
from app.booking.dto.models import (
    BookingRequestDTO,
    BookingRecommendationDTO,
    RecommendedBookingDTO,
    AuditDTO,
)


class BookingDecisionContext:
    """Immutable Decision Context holding parameters during calculation runs."""

    def __init__(
        self,
        correlation_id: str,
        request: BookingRequestDTO,
        journey: Any = None,
        candidates: List[Any] = None,
        availability: Dict[str, Any] = None,
        confirmation: Dict[str, Any] = None,
        quota_rec: Dict[str, Any] = None,
        boarding_rec: Dict[str, Any] = None,
        booking_risk: Dict[str, Any] = None,
        booking_score: Dict[str, Any] = None,
        strategy_result: Dict[str, Any] = None,
        recommendation: Optional[BookingRecommendationDTO] = None,
    ):
        self.correlation_id = correlation_id
        self.request = request
        self.journey = journey
        self.candidates = candidates or []
        self.availability = availability or {}
        self.confirmation = confirmation or {}
        self.quota_rec = quota_rec or {}
        self.boarding_rec = boarding_rec or {}
        self.booking_risk = booking_risk or {}
        self.booking_score = booking_score or {}
        self.strategy_result = strategy_result or {}
        self.recommendation = recommendation

    def copy_with(self, **kwargs) -> "BookingDecisionContext":
        return BookingDecisionContext(
            correlation_id=kwargs.get("correlation_id", self.correlation_id),
            request=kwargs.get("request", self.request),
            journey=kwargs.get("journey", self.journey),
            candidates=kwargs.get("candidates", self.candidates),
            availability=kwargs.get("availability", self.availability),
            confirmation=kwargs.get("confirmation", self.confirmation),
            quota_rec=kwargs.get("quota_rec", self.quota_rec),
            boarding_rec=kwargs.get("boarding_rec", self.boarding_rec),
            booking_risk=kwargs.get("booking_risk", self.booking_risk),
            booking_score=kwargs.get("booking_score", self.booking_score),
            strategy_result=kwargs.get("strategy_result", self.strategy_result),
            recommendation=kwargs.get("recommendation", self.recommendation),
        )


class BookingDecisionContextFactory:
    """Centralized Factory for creating and validating BookingDecisionContext."""

    @staticmethod
    def create_context(
        request: BookingRequestDTO, correlation_id: str, journey: Any = None
    ) -> BookingDecisionContext:
        # Enforce validation invariants
        if not request.traveler_id:
            raise ValueError("Traveler ID is required in request.")
        if not request.journey_id:
            raise ValueError("Journey ID is required in request.")
        if not correlation_id:
            raise ValueError("Correlation ID is required.")

        return BookingDecisionContext(
            correlation_id=correlation_id, request=request, journey=journey
        )


class BookingCoordinator(IBookingCoordinator):
    def __init__(
        self,
        candidate_builder: IBookingCandidateBuilder,
        availability_engine: IAvailabilityEngine,
        confirmation_engine: IConfirmationEngine,
        quota_engine: IQuotaEngine,
        boarding_engine: IBoardingEngine,
        constraint_engine: IConstraintEngine,
        risk_engine: IRiskEngine,
        scoring_engine: IScoringEngine,
        ranking_engine: IRankingEngine,
        conflict_resolver: IConflictResolutionEngine,
        explanation_engine: IExplanationEngine,
        recommendation_engine: IRecommendationEngine,
        audit_engine: IAuditEngine,
        metrics_engine: IMetricsEngine,
        event_publisher: IEventPublisher,
    ):
        self.candidate_builder = candidate_builder
        self.availability_engine = availability_engine
        self.confirmation_engine = confirmation_engine
        self.quota_engine = quota_engine
        self.boarding_engine = boarding_engine
        self.constraint_engine = constraint_engine
        self.risk_engine = risk_engine
        self.scoring_engine = scoring_engine
        self.ranking_engine = ranking_engine
        self.conflict_resolver = conflict_resolver
        self.explanation_engine = explanation_engine
        self.recommendation_engine = recommendation_engine
        self.audit_engine = audit_engine
        self.metrics_engine = metrics_engine
        self.event_publisher = event_publisher

    async def coordinate_decision(
        self, context: BookingDecisionContext
    ) -> BookingRecommendationDTO:
        start_time = time.time()

        # 1. Candidate Builder
        t_cb = time.time()
        candidates = self.candidate_builder.build_booking_candidates(
            context.journey, context.request.preferences
        )
        self.metrics_engine.increment_metric(
            "candidate_builder_latency_ms", (time.time() - t_cb) * 1000
        )

        # 2. Availability Engine
        t_av = time.time()
        availability_map = await self.availability_engine.verify_availability(
            candidates
        )
        self.metrics_engine.increment_metric(
            "availability_latency_ms", (time.time() - t_av) * 1000
        )

        # 3. Constraint checking & pruning
        pruned_candidates = self.constraint_engine.prune_candidates(
            candidates, context.request.preferences
        )

        scored_recommended_bookings = []

        for candidate in pruned_candidates:
            # 4. Confirmation Engine
            avail = availability_map.get(candidate.candidate_id)
            if not avail:
                continue
            confirmation_dto = self.confirmation_engine.evaluate_confirmation(avail)

            # 5. Quota Engine
            self.quota_engine.resolve_quotas(context.request.preferences, avail)

            # 6. Boarding Engine
            boarding_dto = self.boarding_engine.optimize_boarding(
                candidate, context.request.preferences
            )

            # 7. Risk Engine
            risk_dto = self.risk_engine.calculate_risk(
                candidate, avail, confirmation_dto, boarding_dto
            )

            # 8. Scoring Engine
            score_dto = self.scoring_engine.compute_booking_score(
                candidate,
                avail,
                confirmation_dto,
                risk_dto,
                context.request.preferences.get("weights", {}),
            )

            # 9. Explanation Engine
            explanation_dto = self.explanation_engine.generate_explanations(
                candidate, score_dto, risk_dto, context.request.preferences
            )

            scored_recommended_bookings.append(
                RecommendedBookingDTO(
                    candidate_id=candidate.candidate_id,
                    candidate=candidate,
                    score=score_dto,
                    risk=risk_dto,
                    explanation=explanation_dto.model_dump(),
                    strategy_tag="DEFAULT",
                )
            )

        # 10. Conflict Resolution
        resolved_bookings = self.conflict_resolver.resolve_conflicts(
            scored_recommended_bookings, context.request.preferences
        )

        # 11. Ranking Engine
        ranked_bookings = self.ranking_engine.rank_candidates(
            resolved_bookings, context.request.preferences.get("weights", {})
        )

        primary = ranked_bookings[0] if ranked_bookings else None
        alternatives = ranked_bookings[1:] if len(ranked_bookings) > 1 else []

        # 12. Compile Recommendation DTO
        recommendation_dto = await self.recommendation_engine.compile_recommendations(
            primary, alternatives, context.correlation_id
        )

        # 13. Audit Logging
        audit_id = f"aud_bkg_{uuid.uuid4().hex[:8]}"
        audit_record = AuditDTO(
            booking_decision_id=audit_id,
            recommendation_id=recommendation_dto.recommendation_id,
            correlation_id=context.correlation_id,
            timestamp=time.time(),
            rule_version="1.0.0",
            strategy_used="DEFAULT",
            score_breakdown=primary.score.model_dump() if primary else {},
            risk_breakdown=primary.risk.model_dump() if primary else {},
            confidence=primary.score.confirmation_subscore / 100.0 if primary else 0.0,
            reason_codes=primary.explanation.get("reason_codes", []) if primary else [],
            supporting_evidence=primary.explanation.get("score_breakdown", {})
            if primary
            else {},
            decision_outcome="GENERATED",
        )
        await self.audit_engine.log_decision(audit_record)

        # 14. Event Dispatching
        await self.event_publisher.publish_event(
            "BookingRecommended",
            {
                "recommendation_id": recommendation_dto.recommendation_id,
                "correlation_id": context.correlation_id,
                "timestamp": recommendation_dto.generated_at,
            },
        )

        self.metrics_engine.increment_metric(
            "booking_pipeline_latency_ms", (time.time() - start_time) * 1000
        )

        return recommendation_dto


class BookingIntelligenceGateway(IBookingGateway):
    def __init__(self, coordinator: IBookingCoordinator):
        self.coordinator = coordinator

    async def process_booking_query(
        self, request: BookingRequestDTO, correlation_id: str
    ) -> BookingRecommendationDTO:
        # Construct the context using the Factory
        # Journey parameters represents physical base tracks (simulate loading journey tracks)
        journey_mock = {"journey_id": request.journey_id, "distance": 700}
        context = BookingDecisionContextFactory.create_context(
            request, correlation_id, journey_mock
        )

        return await self.coordinator.coordinate_decision(context)
