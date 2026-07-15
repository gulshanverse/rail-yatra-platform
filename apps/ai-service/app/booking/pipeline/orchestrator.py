# app/booking/pipeline/orchestrator.py
from typing import Any
from app.booking.gateway.coordinator import BookingCoordinator


class BookingPipelineOrchestrator:
    def __init__(self, coordinator: BookingCoordinator):
        self.coordinator = coordinator

    async def execute(self, context: Any) -> Any:
        return await self.coordinator.coordinate_decision(context)
