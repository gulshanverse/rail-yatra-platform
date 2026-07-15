# app/journey/gateway/coordinator.py
import time
import uuid
from typing import List, Dict, Any, Optional
from app.journey.interfaces.contracts import (
    IJourneyGateway,
    IJourneyCandidateBuilder,
    IConstraintEngine,
    IRouteAnalyzer,
    ITransferAnalyzer,
    IRiskEngine,
    IScoringEngine,
    IRankingEngine,
    IExplanationEngine,
    IAuditEngine,
    IMetricsEngine,
    IEventPublisher,
)
from app.journey.dto.models import (
    JourneyQueryDTO,
    JourneyRecommendationDTO,
    RecommendedJourneyDTO,
)


class JourneyDecisionContext:
    """Immutable Decision Context holding parameters during computation runs."""

    def __init__(
        self,
        correlation_id: str,
        query: JourneyQueryDTO,
        candidates: List[Any] = None,
        scores: Dict[str, Any] = None,
        risks: Dict[str, Any] = None,
        explanations: Dict[str, Any] = None,
        recommendation: Optional[JourneyRecommendationDTO] = None,
    ):
        self.correlation_id = correlation_id
        self.query = query
        self.candidates = candidates or []
        self.scores = scores or {}
        self.risks = risks or {}
        self.explanations = explanations or {}
        self.recommendation = recommendation

    def copy_with(self, **kwargs) -> "JourneyDecisionContext":
        return JourneyDecisionContext(
            correlation_id=kwargs.get("correlation_id", self.correlation_id),
            query=kwargs.get("query", self.query),
            candidates=kwargs.get("candidates", self.candidates),
            scores=kwargs.get("scores", self.scores),
            risks=kwargs.get("risks", self.risks),
            explanations=kwargs.get("explanations", self.explanations),
            recommendation=kwargs.get("recommendation", self.recommendation),
        )


class JourneyIntelligenceGateway(IJourneyGateway):
    def __init__(
        self,
        candidate_builder: IJourneyCandidateBuilder,
        constraint_engine: IConstraintEngine,
        route_analyzer: IRouteAnalyzer,
        transfer_analyzer: ITransferAnalyzer,
        risk_engine: IRiskEngine,
        scoring_engine: IScoringEngine,
        ranking_engine: IRankingEngine,
        explanation_engine: IExplanationEngine,
        audit_engine: IAuditEngine,
        metrics_engine: IMetricsEngine,
        event_publisher: IEventPublisher,
    ):
        self.candidate_builder = candidate_builder
        self.constraint_engine = constraint_engine
        self.route_analyzer = route_analyzer
        self.transfer_analyzer = transfer_analyzer
        self.risk_engine = risk_engine
        self.scoring_engine = scoring_engine
        self.ranking_engine = ranking_engine
        self.explanation_engine = explanation_engine
        self.audit_engine = audit_engine
        self.metrics_engine = metrics_engine
        self.event_publisher = event_publisher

    async def process_journey_query(
        self, query: JourneyQueryDTO, correlation_id: str
    ) -> JourneyRecommendationDTO:
        start_time = time.time()

        # Enforce validation invariants
        if query.origin == query.destination:
            raise ValueError("Origin cannot match destination.")

        # 1. candidate building
        t_cb_start = time.time()
        candidates = await self.candidate_builder.build_candidates(
            query.origin,
            query.destination,
            query.earliest_departure,
            query.latest_arrival,
        )
        self.metrics_engine.record_metrics(
            "candidate_builder_latency_ms", (time.time() - t_cb_start) * 1000
        )

        # 2. constraint checking
        pruned_candidates = self.constraint_engine.evaluate_constraints(
            candidates, query.traveler_profile
        )

        scored_recommended_journeys = []

        for candidate in pruned_candidates:
            # 3. Route Analyzer
            t_route_start = time.time()
            route_intel = await self.route_analyzer.analyze_route(candidate)
            self.metrics_engine.record_metrics(
                "route_analyzer_latency_ms", (time.time() - t_route_start) * 1000
            )

            # 4. Transfer Analyzer
            transfer_intel = self.transfer_analyzer.evaluate_transfers(
                candidate, query.traveler_profile
            )

            # 5. Risk Engine
            risk_dto = self.risk_engine.calculate_risk(
                candidate, route_intel, transfer_intel, query.traveler_profile
            )

            # 6. Scoring Engine
            score_dto = self.scoring_engine.compute_scores(
                candidate,
                risk_dto,
                route_intel,
                transfer_intel,
                query.preference_weights,
            )

            # 7. Explanation Engine
            explanation_dto = self.explanation_engine.generate_explanation(
                candidate, score_dto, risk_dto, query.traveler_profile
            )

            # Assemble rated candidate wrapper
            scored_recommended_journeys.append(
                RecommendedJourneyDTO(
                    journey_id=candidate.journey_id,
                    candidate=candidate,
                    score=score_dto,
                    risk=risk_dto,
                    explanation=explanation_dto,
                    strategy_tag="BEST_ITINERARY",
                    confidence_score=score_dto.confidence_subscore,
                )
            )

        # 8. Presentation Ranking
        recommendation_dto = self.ranking_engine.rank_recommendations(
            scored_recommended_journeys, query.preference_weights
        )

        # Enrich correlation metadata parameters
        recommendation_dto.correlation_id = correlation_id
        recommendation_dto.generated_at = time.time()

        # 9. Write audit record
        audit_id = f"aud_{uuid.uuid4().hex[:8]}"
        await self.audit_engine.write_audit_record(
            audit_id,
            recommendation_dto.recommendation_id,
            correlation_id,
            {
                "query": query.model_dump(mode="json"),
                "primary": recommendation_dto.primary_candidate.model_dump(mode="json")
                if recommendation_dto.primary_candidate
                else None,
                "latency_ms": (time.time() - start_time) * 1000,
            },
        )

        # 10. Publish Domain Event
        await self.event_publisher.publish_journey_event(
            "RecommendationGenerated",
            {
                "recommendation_id": recommendation_dto.recommendation_id,
                "correlation_id": correlation_id,
                "timestamp": recommendation_dto.generated_at,
            },
        )

        # Telemetry
        self.metrics_engine.record_metrics(
            "journey_pipeline_latency_ms", (time.time() - start_time) * 1000
        )

        return recommendation_dto
