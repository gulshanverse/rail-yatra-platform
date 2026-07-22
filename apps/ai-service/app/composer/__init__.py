"""
RailYatra AI Response Composer & Explainability Platform (Milestone 6.6).
Provides multi-source response synthesis, multi-tiered explainability, confidence calibration,
conflict arbitration, and DPDP privacy-compliant passenger communications.
"""

from app.composer.config import ComposerConfig, default_composer_config
from app.composer.exceptions import (
    ComposerSystemException,
    ConsentMissingForCompositionException,
    ArbitrationFailedException,
    UpstreamTimeoutException,
    CompositionInvariantViolation,
    PIIMaskingException,
    ExplanationDepthException,
    ResponseValidationException,
    IllegalCompositionStateTransition,
)
from app.composer.state_machine import CompositionStateMachine, CompositionState
from app.composer.telemetry import ComposerTelemetryCollector, telemetry_collector
from app.composer.feature_flags import FeatureFlagRegistry, feature_flags

__all__ = [
    "ComposerConfig",
    "default_composer_config",
    "ComposerSystemException",
    "ConsentMissingForCompositionException",
    "ArbitrationFailedException",
    "UpstreamTimeoutException",
    "CompositionInvariantViolation",
    "PIIMaskingException",
    "ExplanationDepthException",
    "ResponseValidationException",
    "IllegalCompositionStateTransition",
    "CompositionStateMachine",
    "CompositionState",
    "ComposerTelemetryCollector",
    "telemetry_collector",
    "FeatureFlagRegistry",
    "feature_flags",
]
