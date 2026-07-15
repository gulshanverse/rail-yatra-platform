# app/integration/adapters/confirmtkt.py
import logging
from typing import Dict, Any, Type
from pydantic import BaseModel
from app.integration.adapters.base import BaseProviderAdapter
from app.integration.models import (
    PNRStatusResponse,
    PassengerStatus,
    PlatformInfoResponse,
    CoachPositionResponse,
    CoachLayout,
)
from app.integration.exceptions import ProviderValidationError, ProviderBusinessError

logger = logging.getLogger("ai-service.integration.adapters.confirmtkt")


class ConfirmTktAdapter(BaseProviderAdapter):
    @property
    def provider_id(self) -> str:
        return "confirmtkt_gds"

    async def execute_query(
        self, capability: str, params: Dict[str, Any], response_model: Type[BaseModel]
    ) -> BaseModel:
        # Simulate network request headers resolution
        headers = await self.auth_manager.get_auth_headers(self.provider_id)
        logger.debug(f"Executed auth flow with headers: {list(headers.keys())}")

        if capability == "pnr_lookup":
            pnr = params.get("pnr")
            if not pnr or len(pnr) != 10 or not pnr.isdigit():
                raise ProviderValidationError("PNR must be a 10-digit numeric string")

            # Mock GDS response dictionary (simulating direct ConfirmTkt JSON response)
            raw_response = {
                "pnr": pnr,
                "trainNo": "12002",
                "trainName": "Bhopal Shatabdi",
                "journeyDate": "2026-07-28",
                "class": "CC",
                "chartStatus": "Chart Prepared",
                "passengersList": [
                    {"no": 1, "booking": "WL 15", "current": "CNF (Coach C1, Berth 12)"}
                ],
                "prob": "100.0%",
                "delay": "10 mins",
            }

            # Normalization logic matching §15 DTO format
            try:
                passengers = [
                    PassengerStatus(
                        passenger_number=p["no"],
                        booking_status=p["booking"],
                        current_status=p["current"],
                    )
                    for p in raw_response["passengersList"]
                ]

                dto = PNRStatusResponse(
                    pnr=raw_response["pnr"],
                    train_number=raw_response["trainNo"],
                    train_name=raw_response["trainName"],
                    journey_date=raw_response["journeyDate"],
                    booking_class=raw_response["class"],
                    chart_status=raw_response["chartStatus"],
                    passengers=passengers,
                    confirmation_probability=raw_response["prob"],
                    delay_prediction=raw_response["delay"],
                )
                return dto
            except Exception as e:
                raise ProviderValidationError(f"JSON field parsing failed for PNR: {e}")

        elif capability == "coach_position":
            train_no = params.get("train_number")
            if not train_no:
                raise ProviderValidationError(
                    "Train number is required for coach layout lookup"
                )

            # Mock coach layouts
            dto = CoachPositionResponse(
                train_number=train_no,
                coaches=[
                    CoachLayout(
                        coach_id="ENG", class_type="ENGINE", position_from_engine=0
                    ),
                    CoachLayout(coach_id="C1", class_type="CC", position_from_engine=1),
                    CoachLayout(coach_id="C2", class_type="CC", position_from_engine=2),
                ],
                total_coaches=3,
            )
            return dto

        elif capability == "platform_info":
            train_no = params.get("train_number")
            station = params.get("station_code")
            if not train_no or not station:
                raise ProviderValidationError(
                    "Train number and station code are required"
                )

            dto = PlatformInfoResponse(
                train_number=train_no,
                station_code=station,
                scheduled_platform="Platform 1",
                actual_platform="Platform 1",
            )
            return dto

        raise ProviderBusinessError(
            f"Unsupported capability '{capability}' for ConfirmTkt GDS"
        )
