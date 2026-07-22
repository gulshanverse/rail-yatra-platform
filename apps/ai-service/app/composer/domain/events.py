"""
Domain Events for Milestone 6.6 AI Response Composer Platform.
Immutable events emitted by aggregate roots upon response composition state changes.
"""

from dataclasses import dataclass, field
import time
import uuid
from typing import Dict, Any, List


@dataclass(frozen=True)
class ComposerDomainEvent:
    """Base class for all domain events in the AI Response Composer Platform."""

    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    event_version: int = 1

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp,
            "event_version": self.event_version,
        }


@dataclass(frozen=True)
class ResponseComposedEvent(ComposerDomainEvent):
    """Emitted when a full response composition is successfully synthesized."""

    composition_id: str = ""
    session_id: str = ""
    traveler_id: str = ""
    section_count: int = 0
    latency_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "composition_id": self.composition_id,
                "session_id": self.session_id,
                "traveler_id": self.traveler_id,
                "section_count": self.section_count,
                "latency_ms": self.latency_ms,
            }
        )
        return base


@dataclass(frozen=True)
class ConflictArbitratedEvent(ComposerDomainEvent):
    """Emitted when conflicting upstream intelligence outputs are resolved."""

    arbitration_id: str = ""
    conflicting_sources: List[str] = field(default_factory=list)
    chosen_resolution: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "arbitration_id": self.arbitration_id,
                "conflicting_sources": self.conflicting_sources,
                "chosen_resolution": self.chosen_resolution,
            }
        )
        return base


@dataclass(frozen=True)
class ExplanationGeneratedEvent(ComposerDomainEvent):
    """Emitted when multi-tiered explainability payloads are attached."""

    explanation_id: str = ""
    depth_level: int = 1
    node_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "explanation_id": self.explanation_id,
                "depth_level": self.depth_level,
                "node_count": self.node_count,
            }
        )
        return base


@dataclass(frozen=True)
class LowConfidenceWarningEmittedEvent(ComposerDomainEvent):
    """Emitted when model predictions fall below confidence threshold limits."""

    metric_score: float = 0.0
    threshold: float = 0.60
    warning_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "metric_score": self.metric_score,
                "threshold": self.threshold,
                "warning_message": self.warning_message,
            }
        )
        return base


@dataclass(frozen=True)
class PIICompositionMaskedEvent(ComposerDomainEvent):
    """Emitted when non-consented PII is scrubbed prior to composition."""

    traveler_id: str = ""
    fields_masked_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "traveler_id": self.traveler_id,
                "fields_masked_count": self.fields_masked_count,
            }
        )
        return base


@dataclass(frozen=True)
class SafetyOverrideTriggeredEvent(ComposerDomainEvent):
    """Emitted when an operational emergency overrides standard recommendations."""

    trigger_type: str = ""
    overridden_content_type: str = ""

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update(
            {
                "trigger_type": self.trigger_type,
                "overridden_content_type": self.overridden_content_type,
            }
        )
        return base
