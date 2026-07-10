from abc import ABC, abstractmethod
from typing import List, Optional
from app.data.models import (
    NormalizedTrain,
    NormalizedStation,
    NormalizedSeatAvailability,
    NormalizedPnrStatus,
    NormalizedDelayHistory
)

class BaseRailwayProvider(ABC):
    """
    Abstract interface defining standard methods that all external
    Railway API providers (e.g. IRCTC, NTES, Synthetic sandbox) must implement.
    """
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def search_trains(self, source: str, destination: str) -> List[NormalizedTrain]:
        pass

    @abstractmethod
    async def get_station_details(self, station_code: str) -> Optional[NormalizedStation]:
        pass

    @abstractmethod
    async def get_seat_availability(
        self,
        train_number: str,
        source: str,
        destination: str,
        journey_date: str,
        booking_class: str
    ) -> Optional[NormalizedSeatAvailability]:
        pass

    @abstractmethod
    async def get_pnr_status(self, pnr: str) -> Optional[NormalizedPnrStatus]:
        pass

    @abstractmethod
    async def get_delay_history(self, train_number: str) -> Optional[NormalizedDelayHistory]:
        pass
