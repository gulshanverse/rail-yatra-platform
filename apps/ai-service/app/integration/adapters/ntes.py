# app/integration/adapters/ntes.py
import time
import logging
from typing import Dict, Any, Type
from pydantic import BaseModel
from app.integration.adapters.base import BaseProviderAdapter
from app.integration.models import TrainStatusResponse, StationMovement
from app.integration.exceptions import ProviderValidationError, ProviderBusinessError

logger = logging.getLogger("ai-service.integration.adapters.ntes")


class NTESAdapter(BaseProviderAdapter):
    @property
    def provider_id(self) -> str:
        return "ntes_cris"

    async def execute_query(
        self, capability: str, params: Dict[str, Any], response_model: Type[BaseModel]
    ) -> BaseModel:
        # Generate SSL context / client certificates for direct mTLS
        ssl_ctx = self.auth_manager.configure_ssl_context(self.provider_id)
        logger.debug(f"Resolved SSL context parameters: {ssl_ctx}")

        if capability == "live_train_status":
            train_no = params.get("train_number")
            if not train_no:
                raise ProviderValidationError(
                    "Train number is required for live tracking queries"
                )

            # Mock NTES direct JSON format
            raw_response = {
                "train": train_no,
                "name": "Bhopal Shatabdi",
                "current": "NDLS",
                "timestamp": time.time(),
                "delay": 15,
                "stationsList": [
                    {
                        "code": "NDLS",
                        "name": "New Delhi",
                        "schArr": "06:00",
                        "actArr": "06:00",
                        "schDep": "06:15",
                        "actDep": "06:15",
                        "del": 0,
                        "state": "Arrived",
                    },
                    {
                        "code": "AGC",
                        "name": "Agra Cantt",
                        "schArr": "08:10",
                        "actArr": "08:25",
                        "schDep": "08:12",
                        "actDep": "08:27",
                        "del": 15,
                        "state": "Platform Assigned",
                    },
                ],
            }

            try:
                movements = [
                    StationMovement(
                        station_code=s["code"],
                        station_name=s["name"],
                        scheduled_arrival=s["schArr"],
                        actual_arrival=s["actArr"],
                        scheduled_departure=s["schDep"],
                        actual_departure=s["actDep"],
                        delay_minutes=s["del"],
                        status=s["state"],
                    )
                    for s in raw_response["stationsList"]
                ]

                dto = TrainStatusResponse(
                    train_number=raw_response["train"],
                    train_name=raw_response["name"],
                    current_station=raw_response["current"],
                    last_updated=raw_response["timestamp"],
                    delay_minutes=raw_response["delay"],
                    route_movements=movements,
                )
                return dto
            except Exception as e:
                raise ProviderValidationError(
                    f"JSON field parsing failed for Train Status: {e}"
                )

        raise ProviderBusinessError(
            f"Unsupported capability '{capability}' for CRIS NTES"
        )
