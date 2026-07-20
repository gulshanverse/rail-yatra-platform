# app/execution/interfaces.py
from typing import Protocol, runtime_checkable, Any, List


@runtime_checkable
class IRailwayAdapter(Protocol):
    """Protocol contract defining downstream railway capability integrations."""

    async def verify_availability(
        self, train_number: str, travel_date: str, class_code: str
    ) -> Any:
        """Availability Verification Capability contract."""
        ...

    async def reserve_seat(
        self,
        passenger_id: str,
        train_number: str,
        class_code: str,
        concession_tier: str | None = None,
        passenger_age: int | None = None,
    ) -> Any:
        """Reservation Capability contract."""
        ...

    async def cancel_seat(self, pnr: str, passenger_id: str | None = None) -> Any:
        """Cancellation Capability contract."""
        ...


@runtime_checkable
class IExecutionSessionRepository(Protocol):
    """Protocol contract for persisting and retrieving execution session aggregates."""

    def save(self, session: Any) -> None:
        """Persists the ExecutionSession aggregate state."""
        ...

    def find_by_id(self, session_id: str) -> Any | None:
        """Retrieves an ExecutionSession aggregate by its ID."""
        ...

    def find_by_token(self, token: str) -> Any | None:
        """Retrieves an ExecutionSession aggregate by its execution token."""
        ...


@runtime_checkable
class IEventPublisher(Protocol):
    """Protocol contract for publishing Execution Engine domain events."""

    def publish(self, event: Any) -> None:
        """Dispatches domain events to the platform's event stream."""
        ...

    def get_published_events(self) -> List[Any]:
        """Utility method to inspect published events for auditing or verification."""
        ...


@runtime_checkable
class ISpecification(Protocol):
    """Protocol contract representing a domain specification check."""

    def is_satisfied_by(self, candidate: Any) -> bool:
        """Evaluates whether the given candidate satisfies the specification rules."""
        ...


@runtime_checkable
class IExecutionCoordinator(Protocol):
    """Protocol contract for the application execution coordinator service."""

    async def execute_plan(self, plan: Any, token_value: str) -> Any:
        """Orchestrates plan step dispatch, retries, failure mapping, and compensations."""
        ...
