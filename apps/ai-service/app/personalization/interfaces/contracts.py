# app/personalization/interfaces/contracts.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.personalization.dto import (
    TravelerPreferenceDTO,
    TravelerBehaviorDTO,
    LearningObservationDTO,
    LearningDecisionDTO,
    PreferenceConfidenceDTO,
    PreferenceEvidenceDTO,
    ReasonCodeDTO,
    RecommendationAdaptationDTO,
    PreferenceAuditDTO,
    PreferenceMetricsDTO,
    TravelerPersonalizationContext,
    AIReadyPersonalizationContext,
)


class IPersonalizationGateway(ABC):
    @abstractmethod
    async def personalize(
        self,
        traveler_id: str,
        request_type: str,
        raw_dto: Dict[str, Any],
        correlation_id: str,
    ) -> AIReadyPersonalizationContext:
        pass

    @abstractmethod
    async def ingest_observation(
        self, traveler_id: str, action_type: str, value: Any, correlation_id: str
    ) -> None:
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        pass


class IPersonalizationCoordinator(ABC):
    @abstractmethod
    async def execute(
        self,
        traveler_id: str,
        request_type: str,
        raw_dto: Dict[str, Any],
        correlation_id: str,
    ) -> AIReadyPersonalizationContext:
        pass


class IPersonalizationContextFactory(ABC):
    @abstractmethod
    async def build(
        self, traveler_id: str, correlation_id: str
    ) -> TravelerPersonalizationContext:
        pass


class IPipelineOrchestrator(ABC):
    @abstractmethod
    async def execute(
        self, context: TravelerPersonalizationContext, raw_dto: Dict[str, Any]
    ) -> AIReadyPersonalizationContext:
        pass


class IPreferenceEngine(ABC):
    @abstractmethod
    def resolve(
        self, context: TravelerPersonalizationContext
    ) -> List[TravelerPreferenceDTO]:
        pass

    @abstractmethod
    def update(self, traveler_id: str, preference: TravelerPreferenceDTO) -> None:
        pass

    @abstractmethod
    def reset(self, traveler_id: str, category: Optional[str] = None) -> None:
        pass


class IBehaviorEngine(ABC):
    @abstractmethod
    def evaluate(self, context: TravelerPersonalizationContext) -> TravelerBehaviorDTO:
        pass

    @abstractmethod
    def detect_patterns(self, traveler_id: str) -> List[Dict[str, Any]]:
        pass


class IObservationEngine(ABC):
    @abstractmethod
    def ingest(
        self, traveler_id: str, action_type: str, value: Any
    ) -> LearningObservationDTO:
        pass

    @abstractmethod
    def batch_ingest(
        self, events: List[Dict[str, Any]]
    ) -> List[LearningObservationDTO]:
        pass


class ILearningEngine(ABC):
    @abstractmethod
    def evaluate(
        self, observations: List[LearningObservationDTO], behavior: TravelerBehaviorDTO
    ) -> List[LearningDecisionDTO]:
        pass


class IConfidenceEngine(ABC):
    @abstractmethod
    def calculate(
        self, preference_id: str, observations: int, last_observed: datetime
    ) -> PreferenceConfidenceDTO:
        pass

    @abstractmethod
    def apply_decay(
        self, confidence: PreferenceConfidenceDTO
    ) -> PreferenceConfidenceDTO:
        pass


class IConflictResolutionEngine(ABC):
    @abstractmethod
    def resolve(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        pass

    @abstractmethod
    def detect_conflicts(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[Dict[str, Any]]:
        pass


class IPreferenceInheritanceEngine(ABC):
    @abstractmethod
    def propagate(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        pass


class IPreferenceDependencyEngine(ABC):
    @abstractmethod
    def evaluate(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        pass


class IRecommendationAdaptationEngine(ABC):
    @abstractmethod
    def adapt(
        self, raw_dto: Dict[str, Any], context: TravelerPersonalizationContext
    ) -> RecommendationAdaptationDTO:
        pass


class IReasonCodeEngine(ABC):
    @abstractmethod
    def assign(self, decision_context: Dict[str, Any]) -> ReasonCodeDTO:
        pass

    @abstractmethod
    def lookup(self, reason_code: str) -> ReasonCodeDTO:
        pass


class IExplanationEngine(ABC):
    @abstractmethod
    def explain(
        self, reason_code: ReasonCodeDTO, evidence: PreferenceEvidenceDTO, locale: str
    ) -> Dict[str, Any]:
        pass


class IPolicyResolver(ABC):
    @abstractmethod
    def resolve(self, policy_key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        pass

    @abstractmethod
    def validate(self, policy_key: str, value: Any) -> bool:
        pass


class IStrategyRegistry(ABC):
    @abstractmethod
    def select(self, context: TravelerPersonalizationContext) -> List[Any]:
        pass

    @abstractmethod
    def register(self, name: str, strategy: Any) -> None:
        pass


class IScenarioRegistry(ABC):
    @abstractmethod
    def match(self, context: TravelerPersonalizationContext) -> Optional[Any]:
        pass


class ICacheManager(ABC):
    @abstractmethod
    def get(self, cache_name: str, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def put(self, cache_name: str, key: str, value: Any, ttl_seconds: int) -> None:
        pass

    @abstractmethod
    def invalidate(self, cache_name: str, key: str) -> None:
        pass

    @abstractmethod
    def invalidate_all(self, cache_name: str) -> None:
        pass


class IAuditEngine(ABC):
    @abstractmethod
    def log(self, audit: PreferenceAuditDTO) -> str:
        pass

    @abstractmethod
    def verify(self, audit_id: str) -> bool:
        pass


class IMetricsEngine(ABC):
    @abstractmethod
    def increment(
        self, metric_name: str, tags: Optional[Dict[str, str]] = None
    ) -> None:
        pass

    @abstractmethod
    def observe(
        self, metric_name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        pass


class IHealthEngine(ABC):
    @abstractmethod
    def check(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def check_subsystem(self, subsystem: str) -> Dict[str, Any]:
        pass


class IProfileValidator(ABC):
    @abstractmethod
    def validate_profile(self, traveler_id: str) -> bool:
        pass


class IConsentValidator(ABC):
    @abstractmethod
    def validate_consent(self, traveler_id: str) -> bool:
        pass


class IContextValidator(ABC):
    @abstractmethod
    def validate_context(self, context: TravelerPersonalizationContext) -> bool:
        pass


# Repository interfaces


class ITravelerProfileRepository(ABC):
    @abstractmethod
    def get_by_traveler_id(self, traveler_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_profile(self, traveler_id: str, identity_hash: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete_profile(self, traveler_id: str) -> bool:
        pass


class IPreferenceRepository(ABC):
    @abstractmethod
    def get_by_traveler_id(self, traveler_id: str) -> List[TravelerPreferenceDTO]:
        pass

    @abstractmethod
    def save(self, preference: TravelerPreferenceDTO) -> None:
        pass

    @abstractmethod
    def delete_by_traveler_id(self, traveler_id: str) -> None:
        pass


class IBehaviorRepository(ABC):
    @abstractmethod
    def get_by_traveler_id(self, traveler_id: str) -> Optional[TravelerBehaviorDTO]:
        pass

    @abstractmethod
    def save(self, behavior: TravelerBehaviorDTO) -> None:
        pass


class IObservationRepository(ABC):
    @abstractmethod
    def get_by_traveler_id_and_window(
        self, traveler_id: str, start_time: datetime, end_time: datetime
    ) -> List[LearningObservationDTO]:
        pass

    @abstractmethod
    def save(self, observation: LearningObservationDTO) -> None:
        pass

    @abstractmethod
    def delete_expired(self) -> int:
        pass


class ILearningRepository(ABC):
    @abstractmethod
    def get_active_sessions(self, traveler_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_session(self, session: Dict[str, Any]) -> None:
        pass


class IConfidenceRepository(ABC):
    @abstractmethod
    def get_by_preference_id(
        self, preference_id: str
    ) -> Optional[PreferenceConfidenceDTO]:
        pass

    @abstractmethod
    def save(self, confidence: PreferenceConfidenceDTO) -> None:
        pass


class IReasonCodeRepository(ABC):
    @abstractmethod
    def get_by_code(self, code: str) -> Optional[ReasonCodeDTO]:
        pass


class IPolicyRepository(ABC):
    @abstractmethod
    def get_policy(self, policy_key: str) -> Optional[Dict[str, Any]]:
        pass


class IConfigurationRepository(ABC):
    @abstractmethod
    def get_config(self, key: str) -> Optional[Any]:
        pass


class IAuditRepository(ABC):
    @abstractmethod
    def save(self, audit: PreferenceAuditDTO) -> None:
        pass

    @abstractmethod
    def get_by_id(self, audit_id: str) -> Optional[PreferenceAuditDTO]:
        pass


class IMetricsRepository(ABC):
    @abstractmethod
    def save(self, metric: PreferenceMetricsDTO) -> None:
        pass


class ICacheRepository(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        pass

    @abstractmethod
    def delete(self, key: str) -> None:
        pass


class IEventPublisher(ABC):
    @abstractmethod
    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        pass
