# app/booking/strategy/implementations.py
from typing import List, Any
from app.booking.interfaces.contracts import IStrategy


class HighestConfirmationStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "HIGHEST_CONFIRMATION"

    def evaluate(self, candidates: List[Any]) -> List[Any]:
        return sorted(
            candidates, key=lambda c: c.score.confirmation_subscore, reverse=True
        )


class LowestRiskStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "LOWEST_RISK"

    def evaluate(self, candidates: List[Any]) -> List[Any]:
        return sorted(candidates, key=lambda c: c.risk.connection_failure_probability)


class BudgetStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "BUDGET"

    def evaluate(self, candidates: List[Any]) -> List[Any]:
        return sorted(candidates, key=lambda c: c.score.cost_subscore, reverse=True)


class ComfortStrategy(IStrategy):
    @property
    def strategy_name(self) -> str:
        return "COMFORT"

    def evaluate(self, candidates: List[Any]) -> List[Any]:
        return sorted(candidates, key=lambda c: c.score.comfort_subscore, reverse=True)
