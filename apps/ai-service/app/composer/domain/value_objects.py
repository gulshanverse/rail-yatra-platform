"""
Value Objects for Milestone 6.6 AI Response Composer Domain.
Immutable, self-validating value objects following Domain-Driven Design principles.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any

from app.composer.exceptions import CompositionInvariantViolation


class CertaintyLevel(str, Enum):
    """Quantitative confidence score levels."""

    HIGH = "HIGH"          # 85% - 100%
    MEDIUM = "MEDIUM"      # 60% - 84%
    LOW = "LOW"            # 30% - 59%
    UNCERTAIN = "UNCERTAIN" # < 30%


class PersonaLayoutMode(str, Enum):
    """Adaptive layout density modes based on user persona & context."""

    ULTRA_SHORT = "ULTRA_SHORT"    # < 15 words (Smartwatch / platform glance)
    SHORT = "SHORT"                # 15-40 words (Mobile chat status)
    NORMAL = "NORMAL"              # Standard scannable markdown with cards
    DETAILED = "DETAILED"          # Complete step-by-step breakdown & citations
    EMERGENCY = "EMERGENCY"        # High-emphasis disruption alert banner
    ACCESSIBILITY = "ACCESSIBILITY"# High contrast, simple plain language


class InformationPriority(str, Enum):
    """Information hierarchy levels for composition prioritization."""

    EMERGENCY = "EMERGENCY"  # Safety alerts, derailments, major disruptions
    CRITICAL = "CRITICAL"   # PNR status change, platform changes
    PRIMARY = "PRIMARY"     # Train schedule, fare, waitlist odds
    SECONDARY = "SECONDARY" # Historical trends, meal options
    OPTIONAL = "OPTIONAL"   # Weather, scenic spots
    HIDDEN = "HIDDEN"       # Raw model logs, embeddings


class EmotionalTone(str, Enum):
    """Adaptive emotional tone choices matching passenger context."""

    EMPATHIC = "EMPATHIC"       # High empathy during delays or cancellations
    CALM = "CALM"               # Solution-focused during confusion
    ENCOURAGING = "ENCOURAGING" # Warm and engaging for trip planning
    URGENT = "URGENT"           # Clear, step-by-step for emergencies
    TRANSPARENT = "TRANSPARENT" # Objective explanation for policy refusals


class SourceCredibilityRank(int, Enum):
    """Information source credibility ranking (1 = highest, 5 = lowest)."""

    RANK_1_OFFICIAL_API = 1      # Live station feeds, live PNR status
    RANK_2_OFFICIAL_POLICY = 2   # IRCTC refund rules, quota eligibility
    RANK_3_PREDICTION_ENGINE = 3 # Waitlist confirmation odds, delay forecasts
    RANK_4_TRAVELER_MEMORY = 4   # Saved preferences, historical routes
    RANK_5_LLM_GENERATIVE = 5    # General text synthesis, travel tips


@dataclass(frozen=True)
class ConfidenceMetric:
    """Immutable value object representing statistical certainty (0.00 to 1.00)."""

    score: float
    certainty_level: CertaintyLevel = field(init=False)

    def __post_init__(self):
        if not isinstance(self.score, (int, float)) or not (0.0 <= float(self.score) <= 1.0):
            raise CompositionInvariantViolation(
                f"ConfidenceMetric score must be between 0.0 and 1.0. Got: {self.score}"
            )
        # Derive certainty level based on score boundaries
        score_val = float(self.score)
        if score_val >= 0.85:
            level = CertaintyLevel.HIGH
        elif score_val >= 0.60:
            level = CertaintyLevel.MEDIUM
        elif score_val >= 0.30:
            level = CertaintyLevel.LOW
        else:
            level = CertaintyLevel.UNCERTAIN
        object.__setattr__(self, "certainty_level", level)


@dataclass(frozen=True)
class ActionChip:
    """Immutable value object representing a suggested next-step follow-up action."""

    label: str
    intent_payload: Dict[str, Any] = field(default_factory=dict)
    is_primary: bool = False

    def __post_init__(self):
        if not self.label or not isinstance(self.label, str) or len(self.label.strip()) == 0:
            raise CompositionInvariantViolation("ActionChip label cannot be empty.")


@dataclass(frozen=True)
class PolicyCitation:
    """Immutable value object representing official IRCTC / Railway Board rule grounding."""

    clause_number: str
    policy_title: str
    validity_period: str = "2026-ACTIVE"

    def __post_init__(self):
        if not self.clause_number or not self.policy_title:
            raise CompositionInvariantViolation("PolicyCitation clause and title are required.")


@dataclass(frozen=True)
class ResponseSummary:
    """Immutable value object encapsulating the lead direct answer."""

    concise_answer: str
    word_count: int = field(init=False)

    def __post_init__(self):
        if not self.concise_answer or not isinstance(self.concise_answer, str):
            raise CompositionInvariantViolation("ResponseSummary concise_answer cannot be empty.")
        words = self.concise_answer.strip().split()
        object.__setattr__(self, "word_count", len(words))
