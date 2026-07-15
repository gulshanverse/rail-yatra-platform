# app/booking/strategy/registry.py
from typing import Dict, Any
from app.booking.interfaces.contracts import IStrategy
from app.booking.strategy.implementations import (
    HighestConfirmationStrategy,
    LowestRiskStrategy,
    BudgetStrategy,
    ComfortStrategy,
)


class BookingStrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, IStrategy] = {}
        # Register core implementations
        self.register_strategy(HighestConfirmationStrategy())
        self.register_strategy(LowestRiskStrategy())
        self.register_strategy(BudgetStrategy())
        self.register_strategy(ComfortStrategy())

    def register_strategy(self, strategy: IStrategy) -> None:
        self._strategies[strategy.strategy_name] = strategy

    def get_strategy(self, name: str) -> Any:
        return self._strategies.get(name)

    def list_strategies(self) -> list:
        return list(self._strategies.keys())
