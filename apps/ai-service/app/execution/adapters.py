# app/execution/adapters.py
import logging
import uuid
from typing import Any, Dict
from app.execution.interfaces import IRailwayAdapter

logger = logging.getLogger("ai-service.execution.adapters")


class MockRailwayAdapter(IRailwayAdapter):
    """
    Mock implementation of IRailwayAdapter for verification and testing.
    Simulates external railway partner system operations.
    """

    def __init__(self):
        self.availability_mock_responses: Dict[str, str] = {}
        self.reservation_mock_responses: Dict[str, str] = {}

    async def verify_availability(
        self, train_number: str, travel_date: str, class_code: str
    ) -> Dict[str, Any]:
        """Availability Verification Capability."""
        logger.info(
            f"Executing verify_availability for Train: {train_number}, Date: {travel_date}, Class: {class_code}"
        )

        # Check custom mock response override, otherwise default to AVAILABLE
        key = f"{train_number}@{travel_date}"
        status = self.availability_mock_responses.get(key, "AVAILABLE")

        return {
            "status": status,
            "train_number": train_number,
            "date": travel_date,
            "class": class_code,
            "seats_available": 42 if status == "AVAILABLE" else 0,
        }

    async def reserve_seat(
        self,
        passenger_id: str,
        train_number: str,
        class_code: str,
        concession_tier: str | None = None,
        passenger_age: int | None = None,
    ) -> Dict[str, Any]:
        """Reservation Capability."""
        logger.info(
            f"Executing reserve_seat for Passenger: {passenger_id}, Train: {train_number}, "
            f"Class: {class_code}, Concession: {concession_tier}, Age: {passenger_age}"
        )

        key = f"{passenger_id}@{train_number}"
        if key in self.reservation_mock_responses:
            status = self.reservation_mock_responses[key]
            if status == "FAIL":
                return {
                    "status": "FAILED",
                    "error": "Inventory sold out or partner gateway error",
                }

        pnr = f"PNR-{uuid.uuid4().hex[:10].upper()}"
        return {
            "status": "CONFIRMED",
            "pnr": pnr,
            "train_number": train_number,
            "passenger_id": passenger_id,
            "class": class_code,
            "booking_date": travel_date_placeholder(),
        }

    async def cancel_seat(
        self, pnr: str, passenger_id: str | None = None
    ) -> Dict[str, Any]:
        """Cancellation Capability."""
        logger.info(f"Executing cancel_seat for PNR: {pnr}, Passenger: {passenger_id}")

        refund_id = f"REF-{uuid.uuid4().hex[:10].upper()}"
        return {
            "status": "CANCELLED",
            "pnr": pnr,
            "refund_reference": refund_id,
            "refund_amount": 1200.0,
            "cancellation_fee": 120.0,
        }


def travel_date_placeholder() -> str:
    from datetime import datetime, timedelta

    return (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d")
