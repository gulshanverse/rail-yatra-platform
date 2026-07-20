from typing import Dict, Any, Optional, List


class ApprovedFunctionRegistry:
    """Registry of whitelisted platform services that are approved for planning sequences."""

    def __init__(self):
        self._registry: Dict[str, Dict[str, Any]] = {}
        self._initialize_defaults()

    def register(
        self, function_name: str, input_schema: Dict[str, Any], output_schema: str
    ) -> None:
        """Registers a platform capability to the approved whitelist."""
        self._registry[function_name] = {
            "function_name": function_name,
            "input_schema": input_schema,
            "output_schema": output_schema,
        }

    def is_approved(self, function_name: str) -> bool:
        """Returns True if the function is whitelisted and approved for sequencing."""
        return function_name in self._registry

    def get_metadata(self, function_name: str) -> Optional[Dict[str, Any]]:
        """Returns the inputs/outputs schema contract metadata for the function."""
        return self._registry.get(function_name)

    def _initialize_defaults(self) -> None:
        # Prepopulate with the standard whitelisted functions defined in Planning.md
        defaults: List[tuple[str, Dict[str, Any], str]] = [
            (
                "search_trains",
                {"origin": str, "destination": str, "date": str},
                "List[TrainCanonical]",
            ),
            ("check_pnr", {"pnr": str}, "PNRCanonical"),
            (
                "book_ticket",
                {"train_number": str, "passenger_id": str, "date": str, "class": str},
                "BookingStatus",
            ),
            ("cancel_ticket", {"pnr": str}, "RefundCanonical"),
            (
                "check_seat_availability",
                {"train_number": str, "date": str, "class": str},
                "SeatAvailability",
            ),
            (
                "search_alternative_route",
                {"origin": str, "destination": str, "date": str},
                "List[Route]",
            ),
            (
                "get_fare",
                {"train_number": str, "origin": str, "destination": str, "class": str},
                "FareCanonical",
            ),
            ("check_waitlist_probability", {"pnr": str}, "WaitlistProbability"),
            ("request_clarification", {"missing_slots": list}, "ClarificationResponse"),
        ]
        for name, inputs, outputs in defaults:
            self.register(name, inputs, outputs)


# Global singleton instance for the approved functions whitelist
function_registry = ApprovedFunctionRegistry()
