# app/planner/models.py
from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class PlanStepStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class PlanStatus(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


class Constraint(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_id: str = Field(..., description="Unique rule/constraint identifier")
    description: str = Field(..., description="Description of the constraint")
    category: str = Field(
        ..., description="E.g. regulatory, route_feasibility, group_limit"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Rule evaluation parameters"
    )


class Decision(BaseModel):
    model_config = ConfigDict(frozen=True)

    decision_id: str = Field(..., description="Unique identifier for the decision")
    reason: str = Field(..., description="Reasoning behind this decision outcome")
    selected_option: str = Field(
        ..., description="The chosen scheduling option or action"
    )
    alternatives: List[str] = Field(
        default_factory=list, description="Alternative options evaluated"
    )


class PlanStep(BaseModel):
    step_id: str = Field(..., description="Unique identifier for the plan step")
    sequence_number: int = Field(
        ..., description="Ordering sequence number (starting from 1)"
    )
    function_name: str = Field(
        ..., description="Name of the whitelisted platform function"
    )
    input_args: Dict[str, Any] = Field(
        default_factory=dict, description="Parameters passed to the function"
    )
    expected_output: str = Field(
        ..., description="The expected outcome key for downstream coordination"
    )
    status: PlanStepStatus = Field(default=PlanStepStatus.PENDING)
    prerequisites: List[str] = Field(
        default_factory=list, description="IDs of steps that must finish before this"
    )
    fallback_step_id: Optional[str] = Field(
        default=None, description="Optional step to route to if this fails"
    )
    constraints: List[Constraint] = Field(
        default_factory=list, description="Constraints verified for this step"
    )


class ValidationReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    is_valid: bool = Field(
        ..., description="Indicates if the plan conforms to all rules"
    )
    violated_constraints: List[Constraint] = Field(
        default_factory=list, description="List of constraints failed"
    )
    decisions: List[Decision] = Field(
        default_factory=list, description="Decisions logged during check"
    )
    warnings: List[str] = Field(
        default_factory=list, description="Non-blocking warning messages"
    )


class StructuredTravelPlan(BaseModel):
    plan_id: str = Field(..., description="Unique aggregate identifier")
    trace_id: str = Field(
        ..., description="Correlation ID tracing back to the user prompt"
    )
    status: PlanStatus = Field(default=PlanStatus.DRAFT)
    steps: List[PlanStep] = Field(..., description="Ordered plan steps")
    validation_report: Optional[ValidationReport] = Field(default=None)
    created_at: float = Field(..., description="Creation epoch timestamp")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional debugging metadata"
    )

    @model_validator(mode="after")
    def validate_aggregate_invariants(self) -> "StructuredTravelPlan":
        # 1. At least one step must exist
        if not self.steps:
            raise ValueError("StructuredTravelPlan must contain at least one step.")

        # 2. Unique and ascending sequence numbers
        seq_nums = [step.sequence_number for step in self.steps]
        if seq_nums != sorted(seq_nums):
            raise ValueError(
                "Plan steps must be sorted by sequence_number in ascending order."
            )
        if len(set(seq_nums)) != len(seq_nums):
            raise ValueError("Plan steps must have unique sequence numbers.")

        # 3. Double-booking check: No passenger may have conflicting bookings for overlapping schedules
        passenger_bookings: Dict[str, List[tuple]] = {}
        for step in self.steps:
            if step.function_name == "book_ticket":
                passenger_id = step.input_args.get("passenger_id")
                travel_date = step.input_args.get("date")
                train_number = step.input_args.get("train_number")

                if passenger_id and travel_date and train_number:
                    # Collect bookings per passenger
                    key = f"{passenger_id}@{travel_date}"
                    if key not in passenger_bookings:
                        passenger_bookings[key] = []

                    # If they already have a booking for another train on the same day, check overlap
                    for existing_train in passenger_bookings[key]:
                        if existing_train != train_number:
                            raise ValueError(
                                f"Overlapping booking detected: passenger {passenger_id} has duplicate "
                                f"bookings scheduled for trains {train_number} and {existing_train} on {travel_date}."
                            )
                    passenger_bookings[key].append(train_number)

        return self
