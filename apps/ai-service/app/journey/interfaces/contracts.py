# app/journey/interfaces/contracts.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.journey.dto.models import (
    JourneyQueryDTO,
    JourneyRecommendationDTO,
    JourneyCandidateDTO,
    JourneyScoreDTO,
    JourneyRiskDTO,
    JourneyExplanationDTO,
    RecommendedJourneyDTO,
)


class IJourneyGateway(ABC):
    @abstractmethod
    async def process_journey_query(
        self, query: JourneyQueryDTO, correlation_id: str
    ) -> JourneyRecommendationDTO:
        """
        Coordinates candidate retrieval, validation, evaluations,
        scoring, ranking, explainability, and auditing.
        """
        pass


class IJourneyCandidateBuilder(ABC):
    @abstractmethod
    async def build_candidates(
        self, origin: str, destination: str, earliest_dep: Any, latest_arr: Any
    ) -> List[JourneyCandidateDTO]:
        """
        Assembles single and multi-segment candidate paths
        matching departure windows, constructing the transfer graph.
        """
        pass


class IConstraintEngine(ABC):
    @abstractmethod
    def evaluate_constraints(
        self, candidates: List[JourneyCandidateDTO], traveler_profile: Dict[str, Any]
    ) -> List[JourneyCandidateDTO]:
        """
        Runs candidate journeys through hard filters and soft preferences,
        returning validated candidates.
        """
        pass


class IRouteAnalyzer(ABC):
    @abstractmethod
    async def analyze_route(self, candidate: JourneyCandidateDTO) -> Dict[str, Any]:
        """
        Evaluates track corridor stability, diversion risks,
        and structural complexity profiles.
        """
        pass


class ITransferAnalyzer(ABC):
    @abstractmethod
    def evaluate_transfers(
        self, candidate: JourneyCandidateDTO, traveler_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculates transfer feasibility, minimum connection times,
        and walking time vectors between platforms.
        """
        pass


class IRiskEngine(ABC):
    @abstractmethod
    def calculate_risk(
        self,
        candidate: JourneyCandidateDTO,
        route_intel: Dict[str, Any],
        transfer_intel: Dict[str, Any],
        traveler_profile: Dict[str, Any],
    ) -> JourneyRiskDTO:
        """
        Computes composite delay, cancellation, and connection failure risks.
        """
        pass


class IScoringEngine(ABC):
    @abstractmethod
    def compute_scores(
        self,
        candidate: JourneyCandidateDTO,
        risk: JourneyRiskDTO,
        route_intel: Dict[str, Any],
        transfer_intel: Dict[str, Any],
        weights: Dict[str, float],
    ) -> JourneyScoreDTO:
        """
        Calculates normalized comfort, cost, time, and reliability scores.
        """
        pass


class IStrategy(ABC):
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        pass

    @abstractmethod
    def evaluate(
        self, candidates: List[RecommendedJourneyDTO]
    ) -> List[RecommendedJourneyDTO]:
        """
        Applies strategy-specific weights to filter and sort candidates.
        """
        pass


class IRankingEngine(ABC):
    @abstractmethod
    def rank_recommendations(
        self, scored_candidates: List[RecommendedJourneyDTO], weights: Dict[str, float]
    ) -> JourneyRecommendationDTO:
        """
        Ranks primary candidates, executes tie-breaking, and applies traveler preference overrides.
        """
        pass


class IExplanationEngine(ABC):
    @abstractmethod
    def generate_explanation(
        self,
        candidate: JourneyCandidateDTO,
        score: JourneyScoreDTO,
        risk: JourneyRiskDTO,
        traveler_profile: Dict[str, Any],
    ) -> JourneyExplanationDTO:
        """
        Compiles scoring matrices, constraint traces, and raw evidence
        into structured reason codes and natural language templates.
        """
        pass


class IAuditEngine(ABC):
    @abstractmethod
    async def write_audit_record(
        self,
        decision_id: str,
        recommendation_id: str,
        correlation_id: str,
        data: Dict[str, Any],
    ) -> None:
        """
        Writes execution record asynchronously to database partitions or logs.
        """
        pass


class IMetricsEngine(ABC):
    @abstractmethod
    def record_metrics(
        self, metric_name: str, value: float, tags: Dict[str, str] = None
    ) -> None:
        """
        Increments request counters and updates metrics logs.
        """
        pass


class IEventPublisher(ABC):
    @abstractmethod
    async def publish_journey_event(
        self, event_type: str, payload: Dict[str, Any]
    ) -> None:
        """
        Dispatches typed canonical domain events to routing queues.
        """
        pass
