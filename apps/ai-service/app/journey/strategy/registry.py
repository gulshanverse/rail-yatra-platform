# app/journey/strategy/registry.py
from typing import Dict
from app.journey.interfaces.contracts import IStrategy
from app.journey.strategy.implementations import (
    FastestStrategy,
    CheapestStrategy,
    MostReliableStrategy,
    SafestStrategy
)


class StrategyRegistry:
    def __init__(self):
        self._strategies: Dict[str, IStrategy] = {}
        # Pre-register core strategies
        self.register_strategy(FastestStrategy())
        self.register_strategy(CheapestStrategy())
        self.register_strategy(MostReliableStrategy())
        self.register_strategy(SafestStrategy())

    def register_strategy(self, strategy: IStrategy):
        self._strategies[strategy.strategy_name] = strategy

    def get_strategy(self, name: str) -> IStrategy:
        return self._strategies.get(name)

    def list_strategies(self) -> list:
        return list(self._strategies.keys())
