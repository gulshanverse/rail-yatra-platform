# app/booking/interfaces/contracts.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.booking.dto.models import (
    BookingRequestDTO,
    BookingRecommendationDTO,
    BookingCandidateDTO,
    AvailabilityDTO,
    ConfirmationDTO,
    QuotaDTO,
    BoardingDTO,
    RiskDTO,
    ScoreDTO,
    ExplanationDTO,
    AuditDTO,
)


class IBookingGateway(ABC):
    @abstractmethod
    async def process_booking_query(
        self, request: BookingRequestDTO, correlation_id: str
    ) -> BookingRecommendationDTO:
        """
        Coordinates candidate retrieval, validation, evaluation,
        scoring, ranking, explainability, and auditing.
        """
        pass


class IBookingCoordinator(ABC):
    @abstractmethod
    async def coordinate_decision(self, context: Any) -> BookingRecommendationDTO:
        """
        Runs the sequential processing pipeline stages.
        """
        pass


class IBookingCandidateBuilder(ABC):
    @abstractmethod
    def build_booking_candidates(
        self, journey_dto: Any, profile: Dict[str, Any]
    ) -> List[BookingCandidateDTO]:
        """
        Combines spatial-temporal routes with commercial parameters (quotas, class).
        """
        pass


class IAvailabilityEngine(ABC):
    @abstractmethod
    async def verify_availability(
        self, candidates: List[BookingCandidateDTO]
    ) -> Dict[str, AvailabilityDTO]:
        """
        Loads seat inventories and checks snapshot freshness.
        """
        pass


class IConfirmationEngine(ABC):
    @abstractmethod
    def evaluate_confirmation(self, availability: AvailabilityDTO) -> ConfirmationDTO:
        """
        Calculates waitlist progression reliability.
        """
        pass


class IQuotaEngine(ABC):
    @abstractmethod
    def resolve_quotas(self, profile: Dict[str, Any], seat_pools: Any) -> QuotaDTO:
        """
        Determines concessional class eligibility.
        """
        pass


class IBoardingEngine(ABC):
    @abstractmethod
    def optimize_boarding(
        self, candidate: BookingCandidateDTO, profile: Dict[str, Any]
    ) -> BoardingDTO:
        """
        Calculates alternative boarding station changes.
        """
        pass


class IConstraintEngine(ABC):
    @abstractmethod
    def prune_candidates(
        self, candidates: List[BookingCandidateDTO], profile: Dict[str, Any]
    ) -> List[BookingCandidateDTO]:
        """
        Enforces hard limits (wheelchair compose, budget caps).
        """
        pass


class IRiskEngine(ABC):
    @abstractmethod
    def calculate_risk(
        self,
        candidate: BookingCandidateDTO,
        availability: AvailabilityDTO,
        confirmation: ConfirmationDTO,
        boarding: BoardingDTO,
    ) -> RiskDTO:
        """
        Aggregates connections, waitlists, and boarding risks.
        """
        pass


class IScoringEngine(ABC):
    @abstractmethod
    def compute_booking_score(
        self,
        candidate: BookingCandidateDTO,
        availability: AvailabilityDTO,
        confirmation: ConfirmationDTO,
        risk: RiskDTO,
        weights: Dict[str, float],
    ) -> ScoreDTO:
        """
        Computes composite suitability scoring metric.
        """
        pass


class IStrategy(ABC):
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, candidates: List[Any]) -> List[Any]:
        """
        Applies strategy filter sorts.
        """
        pass


class IRankingEngine(ABC):
    @abstractmethod
    def rank_candidates(
        self, scored_candidates: List[Any], weights: Dict[str, float]
    ) -> List[Any]:
        """
        Applies tie-breaker sort configurations.
        """
        pass


class IConflictResolutionEngine(ABC):
    @abstractmethod
    def resolve_conflicts(
        self, candidates: List[Any], profile: Dict[str, Any]
    ) -> List[Any]:
        """
        Applies strategy priority filters.
        """
        pass


class IRecoveryEngine(ABC):
    @abstractmethod
    async def search_backup_options(
        self, failed_candidate: Any, correlation_id: str
    ) -> List[Any]:
        """
        Runs backup Tatkal queries loops when checkout fails.
        """
        pass


class IRecommendationEngine(ABC):
    @abstractmethod
    async def compile_recommendations(
        self, primary: Any, alternatives: List[Any], correlation_id: str
    ) -> BookingRecommendationDTO:
        """
        Aggregates recommendations lists.
        """
        pass


class IExplanationEngine(ABC):
    @abstractmethod
    def generate_explanations(
        self,
        candidate: BookingCandidateDTO,
        score: ScoreDTO,
        risk: RiskDTO,
        profile: Dict[str, Any],
    ) -> ExplanationDTO:
        """
        Generates logic trace reason summaries.
        """
        pass


class IAuditEngine(ABC):
    @abstractmethod
    async def log_decision(self, audit: AuditDTO) -> None:
        """
        Dispatches async logs metrics.
        """
        pass


class IMetricsEngine(ABC):
    @abstractmethod
    def increment_metric(
        self, name: str, value: float, tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Logs telemetry counts.
        """
        pass


class IHealthEngine(ABC):
    @abstractmethod
    def check_health(self) -> Dict[str, str]:
        """
        Exposes liveness checks.
        """
        pass


class ICacheManager(ABC):
    @abstractmethod
    async def get_cached_recommendation(self, key: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    async def cache_recommendation(
        self, key: str, data: Dict[str, Any], ttl: int
    ) -> None:
        pass


class IEventPublisher(ABC):
    @abstractmethod
    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        """
        Dispatches domain event hashes.
        """
        pass
