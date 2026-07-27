"""
RailYatra Predictive Intelligence Platform - Phase 7 Module.

Consolidates Waitlist Forecasting (FR-1), Arrival Delay Projections (FR-2),
Dynamic Seat Projections (FR-3), Station Congestion Forecasting (FR-4),
Alternative Travel Orchestration (FR-5), Multi-Segment Journey Risk (FR-6),
Proactive Event Alerts (FR-7), Personalized Decision Support (FR-8),
and Natural Language Guidance & Explainability (FR-9).
"""

from app.predictive.interfaces import (
    PredictionType,
    ConfidenceLevel,
    ConsentStatus,
    RiskLevel,
    PassengerProfileContext,
    JourneyContext,
    WaitlistPrediction,
    DelayPrediction,
    SeatAvailabilityProjection,
    StationCongestionForecast,
    RiskEvaluation,
    AlternativeOption,
    AlternativeJourneyRecommendation,
    ProactiveAlert,
    CalibratedPredictionOutput,
    LearningOutcomeSignal,
)
from app.predictive.waitlist import WaitlistForecaster
from app.predictive.delay import ArrivalDelayPredictor
from app.predictive.seat import DynamicSeatProjectionEngine
from app.predictive.congestion import StationCongestionForecaster
from app.predictive.risk import MultiSegmentRiskMonitor
from app.predictive.recommendation import AlternativeTravelOrchestrator
from app.predictive.notification import ProactiveAlertDispatcher
from app.predictive.personalization import PersonalizedDecisionSupportEngine
from app.predictive.explainability import NaturalLanguageGuidanceEngine
from app.predictive.governance import PredictiveGovernanceController
from app.predictive.learning import ContinuousLearningCoordinator
from app.predictive.orchestrator import PredictiveIntelligenceOrchestrator

__all__ = [
    "PredictionType",
    "ConfidenceLevel",
    "ConsentStatus",
    "RiskLevel",
    "PassengerProfileContext",
    "JourneyContext",
    "WaitlistPrediction",
    "DelayPrediction",
    "SeatAvailabilityProjection",
    "StationCongestionForecast",
    "RiskEvaluation",
    "AlternativeOption",
    "AlternativeJourneyRecommendation",
    "ProactiveAlert",
    "CalibratedPredictionOutput",
    "LearningOutcomeSignal",
    "WaitlistForecaster",
    "ArrivalDelayPredictor",
    "DynamicSeatProjectionEngine",
    "StationCongestionForecaster",
    "MultiSegmentRiskMonitor",
    "AlternativeTravelOrchestrator",
    "ProactiveAlertDispatcher",
    "PersonalizedDecisionSupportEngine",
    "NaturalLanguageGuidanceEngine",
    "PredictiveGovernanceController",
    "ContinuousLearningCoordinator",
    "PredictiveIntelligenceOrchestrator",
]
