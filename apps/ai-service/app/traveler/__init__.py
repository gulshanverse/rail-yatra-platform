# app/traveler/__init__.py
"""
Traveler Assistance & Proactive Intelligence Platform – Public API.

Milestone 5.5 implementation surface.
"""

from app.traveler.dto.models import (
    TravelerEventDTO,
    TravelerActionDTO,
    TravelerExplanationDTO,
    TravelerGuidanceDTO,
    TravelerAlertDTO,
    TravelerReminderDTO,
    TravelerRecoveryDTO,
    TravelerCheckpointDTO,
    TravelerTimelineDTO,
    TravelerAuditDTO,
    TravelerMetricsDTO,
)
from app.traveler.interfaces.contracts import (
    ITravelerGateway,
    ITravelerCoordinator,
    ITravelerDecisionContextFactory,
    IPipelineOrchestrator,
    IEventEngine,
    ITimelineEngine,
    ICheckpointEngine,
    IAlertEngine,
    IReminderEngine,
    IGuidanceEngine,
    IRecommendationEngine,
    IRecoveryEngine,
    IActionEngine,
    IRiskEngine,
    IPriorityEngine,
    ISuppressionEngine,
    IEscalationEngine,
    IExplanationEngine,
    IConfidenceEngine,
    IAuditEngine,
    IMetricsEngine,
    IHealthEngine,
    IScenarioEngine,
    IPolicyResolver,
    ICacheManager,
    IEventPublisher,
)
from app.traveler.gateway.coordinator import (
    TravelerDecisionContext,
    TravelerDecisionContextFactory,
    TravelerCoordinator,
    TravelerAssistanceGateway,
)
from app.traveler.pipeline.orchestrator import TravelerPipelineOrchestrator
from app.traveler.timeline.engine import TimelineEngine
from app.traveler.timeline.checkpoint import CheckpointEngine
from app.traveler.alerts.alert_engine import AlertEngine
from app.traveler.alerts.reminder_engine import ReminderEngine
from app.traveler.alerts.guidance_engine import GuidanceEngine
from app.traveler.strategy.recovery_engine import RecoveryEngine
from app.traveler.strategy.action_engine import (
    ActionEngine,
    TravelerStrategyRegistry,
    ITravelerStrategy,
)
from app.traveler.strategy.scenario_registry import ScenarioRegistry
from app.traveler.risk.risk_engine import RiskEngine
from app.traveler.risk.confidence_engine import ConfidenceEngine
from app.traveler.risk.priority import (
    PriorityEngine,
    SuppressionEngine,
    EscalationEngine,
)
from app.traveler.policy.resolver import PolicyResolver
from app.traveler.explanation.engine import ExplanationEngine
from app.traveler.cache.manager import TravelerCacheManager
from app.traveler.events.publisher import TravelerEventPublisher
from app.traveler.events.event_engine import EventEngine
from app.traveler.audit.logger import AuditEngine
from app.traveler.metrics.collector import MetricsEngine
from app.traveler.health.checker import HealthEngine
from app.traveler.errors import (
    TravelerError,
    ContextError,
    TimelineError,
    CheckpointError,
    AlertError,
    RecoveryError,
    ExplanationError,
    PolicyError,
)

__all__ = [
    # DTOs
    "TravelerEventDTO",
    "TravelerActionDTO",
    "TravelerExplanationDTO",
    "TravelerGuidanceDTO",
    "TravelerAlertDTO",
    "TravelerReminderDTO",
    "TravelerRecoveryDTO",
    "TravelerCheckpointDTO",
    "TravelerTimelineDTO",
    "TravelerAuditDTO",
    "TravelerMetricsDTO",
    # Interfaces
    "ITravelerGateway",
    "ITravelerCoordinator",
    "ITravelerDecisionContextFactory",
    "IPipelineOrchestrator",
    "IEventEngine",
    "ITimelineEngine",
    "ICheckpointEngine",
    "IAlertEngine",
    "IReminderEngine",
    "IGuidanceEngine",
    "IRecommendationEngine",
    "IRecoveryEngine",
    "IActionEngine",
    "IRiskEngine",
    "IPriorityEngine",
    "ISuppressionEngine",
    "IEscalationEngine",
    "IExplanationEngine",
    "IConfidenceEngine",
    "IAuditEngine",
    "IMetricsEngine",
    "IHealthEngine",
    "IScenarioEngine",
    "IPolicyResolver",
    "ICacheManager",
    "IEventPublisher",
    "ITravelerStrategy",
    # Coordinator & Gateway
    "TravelerDecisionContext",
    "TravelerDecisionContextFactory",
    "TravelerCoordinator",
    "TravelerAssistanceGateway",
    # Engines
    "TravelerPipelineOrchestrator",
    "TimelineEngine",
    "CheckpointEngine",
    "AlertEngine",
    "ReminderEngine",
    "GuidanceEngine",
    "RecoveryEngine",
    "ActionEngine",
    "EventEngine",
    "RiskEngine",
    "ConfidenceEngine",
    "PriorityEngine",
    "SuppressionEngine",
    "EscalationEngine",
    "PolicyResolver",
    "ExplanationEngine",
    "TravelerCacheManager",
    "TravelerEventPublisher",
    "AuditEngine",
    "MetricsEngine",
    "HealthEngine",
    # Registries
    "TravelerStrategyRegistry",
    "ScenarioRegistry",
    # Errors
    "TravelerError",
    "ContextError",
    "TimelineError",
    "CheckpointError",
    "AlertError",
    "RecoveryError",
    "ExplanationError",
    "PolicyError",
]
