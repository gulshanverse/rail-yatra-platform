"""
API Router for Phase 7 Predictive Intelligence Platform.
Exposes endpoints for Waitlist forecasting, Delay projections, Risk evaluation,
Alternative journey orchestration, Station congestion, and Continuous learning.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.predictive.interfaces import (
    JourneyContext,
    PassengerProfileContext,
    LearningOutcomeSignal,
)
from app.predictive.orchestrator import predictive_orchestrator

router = APIRouter(prefix="/api/predictive", tags=["predictive-intelligence"])


class PredictionJourneyRequest(BaseModel):
    journey: JourneyContext
    passenger: Optional[PassengerProfileContext] = None


@router.post("/waitlist")
async def get_waitlist_forecast(payload: PredictionJourneyRequest):
    try:
        res = await predictive_orchestrator.get_waitlist_confirmation_foresight(
            payload.journey, payload.passenger
        )
        return res.model_dump()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Waitlist forecast failed: {str(e)}")


@router.post("/delay")
async def get_delay_forecast(payload: PredictionJourneyRequest):
    try:
        res = await predictive_orchestrator.get_delay_foresight(
            payload.journey, payload.passenger
        )
        return res.model_dump()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delay forecast failed: {str(e)}")


@router.post("/risk")
async def get_risk_forecast(payload: PredictionJourneyRequest):
    try:
        res = await predictive_orchestrator.get_connection_risk_foresight(
            payload.journey, payload.passenger
        )
        return res.model_dump()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk forecast failed: {str(e)}")


@router.post("/alternatives")
async def get_alternative_orchestration(payload: PredictionJourneyRequest):
    try:
        res = await predictive_orchestrator.get_alternative_orchestration(
            payload.journey, payload.passenger
        )
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alternative orchestration failed: {str(e)}")


@router.get("/congestion/{station_code}")
async def get_station_congestion(station_code: str, arrival_hour: int = 14):
    try:
        res = await predictive_orchestrator.get_station_congestion_foresight(
            station_code, arrival_hour
        )
        return res.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Station congestion forecast failed: {str(e)}")


@router.post("/foresight")
async def get_full_foresight_package(payload: PredictionJourneyRequest):
    try:
        res = await predictive_orchestrator.execute_full_journey_foresight_package(
            payload.journey, payload.passenger
        )
        if "error" in res:
            raise HTTPException(status_code=403, detail=res["message"])
        return res
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Foresight package execution failed: {str(e)}")


@router.post("/feedback")
async def register_outcome_signal(signal: LearningOutcomeSignal):
    try:
        res = predictive_orchestrator.register_outcome_signal(signal)
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Outcome registration failed: {str(e)}")


@router.get("/health")
async def get_predictive_health():
    learning_metrics = predictive_orchestrator.get_learning_metrics()
    return {
        "status": "HEALTHY",
        "phase": "7 - Predictive Intelligence Platform",
        "capabilities_active": [
            "FR-1 Waitlist Probability",
            "FR-2 Arrival Delay Projections",
            "FR-3 Dynamic Seat Projections",
            "FR-4 Station Congestion Forecasting",
            "FR-5 Alternative Travel Orchestration",
            "FR-6 Multi-Segment Journey Risk",
            "FR-7 Proactive Event Alerts",
            "FR-8 Personalized Decision Support",
            "FR-9 Natural Language Guidance",
        ],
        "learning_metrics": learning_metrics,
    }
