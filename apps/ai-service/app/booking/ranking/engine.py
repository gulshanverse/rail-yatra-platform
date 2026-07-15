# app/booking/ranking/engine.py
from typing import List, Dict, Any
from app.booking.interfaces.contracts import IRankingEngine


class RankingEngine(IRankingEngine):
    def rank_candidates(
        self, scored_candidates: List[Any], weights: Dict[str, float]
    ) -> List[Any]:
        if not scored_candidates:
            return []

        # Tie-breaker sorting function
        # Priority sort:
        # 1. Overall Score descending
        # 2. Confirmation subscore descending
        # 3. Cost subscore descending (cheaper first)
        # 4. Connection fail probability ascending
        def sort_key(item: Any):
            return (
                -item.score.overall_score,
                -item.score.confirmation_subscore,
                -item.score.cost_subscore,
                item.risk.connection_failure_probability,
            )

        return sorted(scored_candidates, key=sort_key)
