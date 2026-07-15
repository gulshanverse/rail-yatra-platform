# app/journey/strategy/implementations.py
from typing import List
from app.journey.interfaces.contracts import IStrategy
from app.journey.dto.models import RecommendedJourneyDTO


class FastestStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "FASTEST"

    def evaluate(
        self, candidates: List[RecommendedJourneyDTO]
    ) -> List[RecommendedJourneyDTO]:
        # Sort ascending by duration
        return sorted(candidates, key=lambda c: c.candidate.scheduled_duration_minutes)


class CheapestStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "CHEAPEST"

    def evaluate(
        self, candidates: List[RecommendedJourneyDTO]
    ) -> List[RecommendedJourneyDTO]:
        # Sort ascending by cost subscore (meaning higher cost subscore = cheaper route)
        return sorted(candidates, key=lambda c: c.score.cost_subscore, reverse=True)


class MostReliableStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "MOST_RELIABLE"

    def evaluate(
        self, candidates: List[RecommendedJourneyDTO]
    ) -> List[RecommendedJourneyDTO]:
        # Sort descending by reliability
        return sorted(
            candidates, key=lambda c: c.score.reliability_subscore, reverse=True
        )


class SafestStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "SAFEST"

    def evaluate(
        self, candidates: List[RecommendedJourneyDTO]
    ) -> List[RecommendedJourneyDTO]:
        # Sort descending by safety
        return sorted(candidates, key=lambda c: c.score.safety_subscore, reverse=True)
