# app/booking/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class IBookingRepository(ABC):
    @abstractmethod
    async def save_booking(self, booking_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_booking(self, booking_id: str) -> Optional[Dict[str, Any]]:
        pass


class IRecommendationRepository(ABC):
    @abstractmethod
    async def save_recommendation(self, rec_id: str, data: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_recommendation(self, rec_id: str) -> Optional[Dict[str, Any]]:
        pass


class IAuditRepository(ABC):
    @abstractmethod
    async def save_audit(self, audit_id: str, data: Dict[str, Any]) -> None:
        pass
