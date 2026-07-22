"""
Domain Entities for Milestone 6.6 AI Response Composer Platform.
Identity-bearing domain concepts encapsulating section elements, reasoning nodes, and turn snapshots.
"""

from dataclasses import dataclass, field
import uuid
import time
from typing import Dict, Any, List

from app.composer.domain.value_objects import (
    InformationPriority,
    SourceCredibilityRank,
)
from app.composer.exceptions import CompositionInvariantViolation


@dataclass
class ComposedSection:
    """Identity-bearing entity representing a distinct section within a composed response."""

    section_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    section_type: str = "SUMMARY"  # SUMMARY, OPTIONS_TABLE, WARNING_BANNER, DETAILS, ACTION_BAR
    content: str = ""
    priority: InformationPriority = InformationPriority.PRIMARY
    is_expandable: bool = False

    def __post_init__(self):
        if not self.content or len(self.content.strip()) == 0:
            raise CompositionInvariantViolation("ComposedSection content cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "section_id": self.section_id,
            "section_type": self.section_type,
            "content": self.content,
            "priority": self.priority.value,
            "is_expandable": self.is_expandable,
        }


@dataclass
class JustificationNode:
    """Identity-bearing entity representing an individual reasoning factor justifying an AI recommendation."""

    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reasoning_factor: str = ""
    evidence_source: str = ""
    credibility_rank: SourceCredibilityRank = SourceCredibilityRank.RANK_3_PREDICTION_ENGINE
    supporting_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.reasoning_factor:
            raise CompositionInvariantViolation("JustificationNode reasoning_factor cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "reasoning_factor": self.reasoning_factor,
            "evidence_source": self.evidence_source,
            "credibility_rank": self.credibility_rank.value,
            "supporting_data": self.supporting_data,
        }


@dataclass
class ResolutionFactor:
    """Entity representing a specific factor evaluated during conflict arbitration."""

    factor_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    factor_name: str = ""
    weight: float = 1.0
    value: str = ""
    explanation: str = ""

    def __post_init__(self):
        if not self.factor_name:
            raise CompositionInvariantViolation("ResolutionFactor factor_name is required.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "factor_id": self.factor_id,
            "factor_name": self.factor_name,
            "weight": self.weight,
            "value": self.value,
            "explanation": self.explanation,
        }


@dataclass
class TradeOffChoice:
    """Entity representing a trade-off evaluation between competing options."""

    choice_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    option_a: str = ""
    option_b: str = ""
    chosen_option: str = ""
    rationale: str = ""
    factors: List[ResolutionFactor] = field(default_factory=list)

    def __post_init__(self):
        if not self.option_a or not self.option_b:
            raise CompositionInvariantViolation("TradeOffChoice requires option_a and option_b.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "choice_id": self.choice_id,
            "option_a": self.option_a,
            "option_b": self.option_b,
            "chosen_option": self.chosen_option,
            "rationale": self.rationale,
            "factors": [f.to_dict() for f in self.factors],
        }


@dataclass
class TurnSnapshot:
    """Entity capturing a single interaction turn in a multi-turn conversation session."""

    turn_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_input: str = ""
    composed_response_ref: str = ""
    intent: str = ""
    timestamp: float = field(default_factory=time.time)

    def __post_init__(self):
        if not self.user_input:
            raise CompositionInvariantViolation("TurnSnapshot user_input cannot be empty.")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "turn_id": self.turn_id,
            "user_input": self.user_input,
            "composed_response_ref": self.composed_response_ref,
            "intent": self.intent,
            "timestamp": self.timestamp,
        }
