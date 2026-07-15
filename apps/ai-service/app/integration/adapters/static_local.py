# app/integration/adapters/static_local.py
import logging
from typing import Dict, Any, Type
from pydantic import BaseModel
from app.integration.adapters.base import BaseProviderAdapter
from app.integration.models import (
    StationInfoResponse,
    ReservationRulesResponse,
    RailwayCircularsResponse,
    CircularDocument,
    TrainScheduleResponse,
    ScheduleStation,
)
from app.integration.exceptions import ProviderValidationError, ProviderBusinessError

logger = logging.getLogger("ai-service.integration.adapters.static_local")


class StaticLocalAdapter(BaseProviderAdapter):
    @property
    def provider_id(self) -> str:
        return "static_local"

    async def execute_query(
        self, capability: str, params: Dict[str, Any], response_model: Type[BaseModel]
    ) -> BaseModel:
        # Static local data is open/public, no authentication headers needed
        logger.debug("Accessing static local database lookup repository.")

        if capability == "station_info":
            station_code = params.get("station_code")
            if not station_code:
                raise ProviderValidationError(
                    "Station code is required for metadata queries"
                )

            code = station_code.strip().upper()
            if code == "NDLS":
                return StationInfoResponse(
                    station_code="NDLS",
                    station_name="New Delhi",
                    division="Delhi",
                    zone="NR",
                    latitude=28.6430,
                    longitude=77.2223,
                    platform_count=16,
                )
            elif code == "BPL":
                return StationInfoResponse(
                    station_code="BPL",
                    station_name="Bhopal Junction",
                    division="Bhopal",
                    zone="WCR",
                    latitude=23.2658,
                    longitude=77.4116,
                    platform_count=6,
                )

            # Generic fallback station
            return StationInfoResponse(
                station_code=code,
                station_name=f"{code} Junction",
                division="Railway Division",
                zone="IR",
                latitude=20.0,
                longitude=78.0,
                platform_count=4,
            )

        elif capability == "reservation_rules":
            return ReservationRulesResponse(
                quota_rules={
                    "GN": "General Quota - Open to all passengers.",
                    "LD": "Ladies Quota - Reserved compartments for solo female travelers.",
                    "TQ": "Tatkal Quota - Last-minute emergency reservation bookings.",
                },
                refund_rules={
                    "CNF": "Full refund minus clerkage fee if cancelled 48 hours prior to departure.",
                    "RAC": "Clerkage charge deducted if cancelled 30 minutes before departure.",
                },
                tatkal_rules={
                    "AC": "Bookings open daily at 10:00 AM IST.",
                    "Non-AC": "Bookings open daily at 11:00 AM IST.",
                },
            )

        elif capability == "railway_circulars":
            return RailwayCircularsResponse(
                circulars=[
                    CircularDocument(
                        circular_id="RB-2025-047",
                        title="Revised Tatkal Booking Guidelines",
                        publish_date="2025-10-14",
                        url="https://indianrailways.gov.in/circulars/RB-2025-047.pdf",
                        category="Commercial Rules",
                    ),
                    CircularDocument(
                        circular_id="RB-2026-012",
                        title="Monsoon Safety Inspection Rules",
                        publish_date="2026-06-01",
                        url="https://indianrailways.gov.in/circulars/RB-2026-012.pdf",
                        category="Safety",
                    ),
                ]
            )

        elif capability == "train_schedule":
            train_no = params.get("train_number")
            if not train_no:
                raise ProviderValidationError(
                    "Train number is required for timetable queries"
                )

            # Mock schedule list
            return TrainScheduleResponse(
                train_number=train_no,
                train_name="Bhopal Shatabdi",
                runs_on=["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
                stations=[
                    ScheduleStation(
                        station_code="NDLS",
                        arrival_time="06:00",
                        departure_time="06:15",
                        distance_km=0,
                        day_number=1,
                    ),
                    ScheduleStation(
                        station_code="AGC",
                        arrival_time="08:10",
                        departure_time="08:12",
                        distance_km=195,
                        day_number=1,
                    ),
                    ScheduleStation(
                        station_code="BPL",
                        arrival_time="14:40",
                        departure_time="14:45",
                        distance_km=701,
                        day_number=1,
                    ),
                ],
            )

        raise ProviderBusinessError(
            f"Unsupported capability '{capability}' for Static Local Adapter"
        )
