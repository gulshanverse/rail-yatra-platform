# app/traveler/interfaces/contracts.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.traveler.dto.models import (
    TravelerGuidanceDTO,
    TravelerEventDTO,
    TravelerAlertDTO,
    TravelerReminderDTO,
    TravelerRecoveryDTO,
    TravelerTimelineDTO,
    TravelerAuditDTO,
)


class ITravelerGateway(ABC):
    @abstractmethod
    async def process_telemetry_update(
        self, telemetry: Dict[str, Any], correlation_id: str
    ) -> TravelerGuidanceDTO:
        pass


class ITravelerCoordinator(ABC):
    @abstractmethod
    async def coordinate_assistance(self, context: Any) -> TravelerGuidanceDTO:
        pass


class ITravelerDecisionContextFactory(ABC):
    @abstractmethod
    def create_context(
        self, request_payload: Dict[str, Any], correlation_id: str
    ) -> Any:
        pass


class IPipelineOrchestrator(ABC):
    @abstractmethod
    async def execute_pipeline(self, context: Any) -> Any:
        pass


class IEventEngine(ABC):
    @abstractmethod
    def parse_raw_event(self, raw: Dict[str, Any]) -> TravelerEventDTO:
        pass


class ITimelineEngine(ABC):
    @abstractmethod
    def evaluate_timeline(self, context: Any) -> TravelerTimelineDTO:
        pass


class ICheckpointEngine(ABC):
    @abstractmethod
    def verify_checkpoints(self, context: Any) -> List[Any]:
        pass


class IAlertEngine(ABC):
    @abstractmethod
    def evaluate_alerts(self, context: Any) -> List[TravelerAlertDTO]:
        pass


class IReminderEngine(ABC):
    @abstractmethod
    def process_reminders(self, context: Any) -> List[TravelerReminderDTO]:
        pass


class IGuidanceEngine(ABC):
    @abstractmethod
    def compile_guidance(self, context: Any) -> TravelerGuidanceDTO:
        pass


class IRecommendationEngine(ABC):
    @abstractmethod
    def generate_recommendations(self, context: Any) -> List[Any]:
        pass


class IRecoveryEngine(ABC):
    @abstractmethod
    async def build_recovery_plan(
        self, incident: Any, context: Any
    ) -> TravelerRecoveryDTO:
        pass


class IActionEngine(ABC):
    @abstractmethod
    def select_action(self, context: Any) -> Any:
        pass


class IRiskEngine(ABC):
    @abstractmethod
    def calculate_risk(self, context: Any) -> Any:
        pass


class IPriorityEngine(ABC):
    @abstractmethod
    def resolve_priority(self, context: Any) -> Any:
        pass


class ISuppressionEngine(ABC):
    @abstractmethod
    def apply_suppression(self, context: Any) -> bool:
        pass


class IEscalationEngine(ABC):
    @abstractmethod
    def check_escalation(self, context: Any) -> bool:
        pass


class IExplanationEngine(ABC):
    @abstractmethod
    def generate_explanation(self, context: Any) -> Any:
        pass


class IConfidenceEngine(ABC):
    @abstractmethod
    def calculate_confidence(self, context: Any) -> float:
        pass


class IAuditEngine(ABC):
    @abstractmethod
    async def log_guidance(self, audit: TravelerAuditDTO) -> None:
        pass


class IMetricsEngine(ABC):
    @abstractmethod
    def increment_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        pass


class IHealthEngine(ABC):
    @abstractmethod
    def check_health(self) -> Dict[str, Any]:
        pass


class IScenarioEngine(ABC):
    @abstractmethod
    def execute_scenario(self, scenario_name: str, context: Any) -> Any:
        pass


class IPolicyResolver(ABC):
    @abstractmethod
    def resolve_policy(self, policy_name: str) -> Dict[str, Any]:
        pass


class ICacheManager(ABC):
    @abstractmethod
    async def get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def set_cached(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        pass


class IEventPublisher(ABC):
    @abstractmethod
    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        pass
