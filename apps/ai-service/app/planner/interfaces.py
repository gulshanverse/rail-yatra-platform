# app/planner/interfaces.py
from typing import Protocol, runtime_checkable, List, Any
from app.orchestrator.types import IntentDescriptor


@runtime_checkable
class ISpecification(Protocol):
    """Protocol contract representing a domain specification check."""

    def is_satisfied_by(self, plan: Any) -> Any:  # Returns SpecificationResult
        """Evaluates whether the given travel plan satisfies the specification rules."""
        ...


@runtime_checkable
class IStepSequencer(Protocol):
    """Protocol contract for the step sequencing domain service."""

    def sequence_steps(
        self, intent_descriptor: IntentDescriptor
    ) -> List[Any]:  # List[PlanStep]
        """Formulates a sequenced list of PlanSteps from intent slots."""
        ...


@runtime_checkable
class IPlanValidator(Protocol):
    """Protocol contract for the plan validator domain service."""

    def validate_plan(self, plan: Any) -> Any:  # Returns ValidationReport
        """Evaluates a StructuredTravelPlan against all registered specifications and policies."""
        ...


@runtime_checkable
class IClarificationHandler(Protocol):
    """Protocol contract for the clarification handler application service."""

    def handle_clarification(
        self, intent_descriptor: IntentDescriptor
    ) -> Any:  # Returns StructuredTravelPlan
        """Assembles a clarification plan requesting missing inputs."""
        ...


@runtime_checkable
class IPlanningCoordinator(Protocol):
    """Protocol contract for the planning coordinator application service."""

    async def coordinate_planning(
        self, intent_descriptor: IntentDescriptor
    ) -> Any:  # Returns StructuredTravelPlan
        """Orchestrates plan generation, validation, and status signing."""
        ...
