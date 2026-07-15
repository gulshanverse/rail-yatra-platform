# app/journey/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class IJourneyRepository(ABC):
    @abstractmethod
    async def get_by_id(self, journey_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_journey(self, journey_id: str, data: Dict[str, Any]) -> None:
        pass


class IRecommendationRepository(ABC):
    @abstractmethod
    async def save_recommendation(self, recommendation_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_recommendation(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        pass


class IAuditRepository(ABC):
    @abstractmethod
    async def save_audit(self, audit_id: str, payload: Dict[str, Any]) -> None:
        pass
