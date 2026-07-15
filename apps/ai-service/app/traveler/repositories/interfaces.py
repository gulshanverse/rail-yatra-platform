# app/traveler/repositories/interfaces.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class ITravelerRepository(ABC):
    @abstractmethod
    async def get_traveler_profile(self, traveler_id: str) -> Optional[Dict[str, Any]]:
        pass


class ITimelineRepository(ABC):
    @abstractmethod
    async def get_timeline(self, timeline_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def save_timeline(self, timeline_id: str, data: Dict[str, Any]) -> None:
        pass


class ICheckpointRepository(ABC):
    @abstractmethod
    async def log_checkpoint(self, checkpoint_id: str, data: Dict[str, Any]) -> None:
        pass


class IAlertRepository(ABC):
    @abstractmethod
    async def save_alert(self, alert_id: str, data: Dict[str, Any]) -> None:
        pass


class IRecoveryRepository(ABC):
    @abstractmethod
    async def save_recovery_plan(self, recovery_id: str, data: Dict[str, Any]) -> None:
        pass


class IGuidanceRepository(ABC):
    @abstractmethod
    async def save_guidance(self, guidance_id: str, data: Dict[str, Any]) -> None:
        pass


class IAuditRepository(ABC):
    @abstractmethod
    async def save_audit(self, audit_id: str, data: Dict[str, Any]) -> None:
        pass
