# app/journey/ranking/engine.py
import time
import uuid
from typing import List, Dict
from app.journey.interfaces.contracts import IRankingEngine
from app.journey.dto.models import RecommendedJourneyDTO, JourneyRecommendationDTO
from app.journey.config.registry import is_feature_enabled


class RankingEngine(IRankingEngine):
    def rank_recommendations(
        self,
        scored_candidates: List[RecommendedJourneyDTO],
        weights: Dict[str, float]
    ) -> JourneyRecommendationDTO:
        if not scored_candidates:
            return JourneyRecommendationDTO(
                recommendation_id=f"rec_empty_{uuid.uuid4().hex[:8]}",
                primary_candidate=None,
                alternative_candidates=[],
                generated_at=time.time(),
                decision_version="1.0.0",
                correlation_id="corr-default"
            )

        # Tie-breaker sorting function
        # Sorting priority:
        # 1. Overall score descending
        # 2. Reliability subscore descending
        # 3. Transfers count ascending
        # 4. Cost subscore descending (higher is cheaper)
        def sort_key(item: RecommendedJourneyDTO):
            return (
                -item.score.overall_score,
                -item.score.reliability_subscore,
                len(item.candidate.transfers),
                -item.score.cost_subscore
            )

        sorted_candidates = sorted(scored_candidates, key=sort_key)

        primary = sorted_candidates[0]
        alternatives = sorted_candidates[1:] if len(sorted_candidates) > 1 else []

        # If experimental ranking flag is enabled, we could re-sort alternatives.
        if is_feature_enabled("FF_ENABLE_EXPERIMENTAL_RANKING"):
            # Mock behavior: move cheaper alternatives higher
            alternatives = sorted(alternatives, key=lambda a: a.score.cost_subscore, reverse=True)

        return JourneyRecommendationDTO(
            recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
            primary_candidate=primary,
            alternative_candidates=alternatives,
            generated_at=time.time(),
            decision_version="1.0.0",
            correlation_id="corr-default"
        )
