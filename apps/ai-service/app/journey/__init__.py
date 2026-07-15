# app/journey/__init__.py
from app.journey.dto.models import (
    JourneyQueryDTO,
    JourneyRecommendationDTO,
    RecommendedJourneyDTO,
    JourneyCandidateDTO,
    SegmentDTO,
    TransferDTO,
    JourneyScoreDTO,
    JourneyRiskDTO,
    JourneyExplanationDTO
)
from app.journey.interfaces.contracts import (
    IJourneyGateway,
    IJourneyCandidateBuilder,
    IConstraintEngine,
    IRouteAnalyzer,
    ITransferAnalyzer,
    IRiskEngine,
    IScoringEngine,
    IRankingEngine,
    IExplanationEngine,
    IAuditEngine,
    IMetricsEngine,
    IEventPublisher
)
from app.journey.config.registry import is_feature_enabled, get_policy
from app.journey.gateway.coordinator import JourneyIntelligenceGateway, JourneyDecisionContext
from app.journey.candidate.builder import JourneyCandidateBuilder
from app.journey.constraints.engine import ConstraintEngine
from app.journey.route.analyzer import RouteAnalyzer
from app.journey.transfer.analyzer import TransferAnalyzer
from app.journey.risk.engine import RiskEngine
from app.journey.scoring.engine import ScoringEngine
from app.journey.strategy.registry import StrategyRegistry
from app.journey.ranking.engine import RankingEngine
from app.journey.explanation.engine import ExplanationEngine
from app.journey.audit.logger import AuditEngine
from app.journey.metrics.collector import MetricsEngine
from app.journey.events.publisher import JourneyEventPublisher

__all__ = [
    # DTOs
    "JourneyQueryDTO",
    "JourneyRecommendationDTO",
    "RecommendedJourneyDTO",
    "JourneyCandidateDTO",
    "SegmentDTO",
    "TransferDTO",
    "JourneyScoreDTO",
    "JourneyRiskDTO",
    "JourneyExplanationDTO",
    # Interfaces
    "IJourneyGateway",
    "IJourneyCandidateBuilder",
    "IConstraintEngine",
    "IRouteAnalyzer",
    "ITransferAnalyzer",
    "IRiskEngine",
    "IScoringEngine",
    "IRankingEngine",
    "IExplanationEngine",
    "IAuditEngine",
    "IMetricsEngine",
    "IEventPublisher",
    # Registry Config
    "is_feature_enabled",
    "get_policy",
    # Implementations
    "JourneyIntelligenceGateway",
    "JourneyDecisionContext",
    "JourneyCandidateBuilder",
    "ConstraintEngine",
    "RouteAnalyzer",
    "TransferAnalyzer",
    "RiskEngine",
    "ScoringEngine",
    "StrategyRegistry",
    "RankingEngine",
    "ExplanationEngine",
    "AuditEngine",
    "MetricsEngine",
    "JourneyEventPublisher",
]
