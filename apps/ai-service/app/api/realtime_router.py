"""
REST API Router for Phase 8 Real-Time Operations Platform.
Exposes endpoints for event ingestion, train state tracking, journey status, dynamic ETA, incidents, notifications, dashboards, and live AI context.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.realtime.orchestrator import RealTimeOperationsOrchestrator

router = APIRouter(prefix="/api/realtime", tags=["realtime-operations"])
orchestrator = RealTimeOperationsOrchestrator()


class RegisterJourneyRequest(BaseModel):
    journey_id: str
    passenger_id: str
    train_number: str
    origin_station: str
    destination_station: str
    scheduled_eta: str


class DispatchNotificationRequest(BaseModel):
    journey_id: str
    title: str
    message: str


@router.post("/events", status_code=201)
async def ingest_event(payload: Dict[str, Any]):
    """Ingests a live operational railway event."""
    try:
        event = await orchestrator.process_raw_event(payload)
        return {
            "status": "INGESTED",
            "event_id": event.event_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal ingestion error: {e}")


@router.post("/journeys/register", status_code=201)

def register_journey(req: RegisterJourneyRequest):
    """Registers an active passenger journey for real-time monitoring."""
    journey = orchestrator.register_passenger_journey(
        journey_id=req.journey_id,
        passenger_id=req.passenger_id,
        train_number=req.train_number,
        origin_station=req.origin_station,
        destination_station=req.destination_station,
        scheduled_eta=req.scheduled_eta,
    )
    return {"status": "REGISTERED", "journey": journey.model_dump()}


@router.get("/trains/{train_number}")

def get_train_state(train_number: str):
    """Returns authoritative live operational state for a train."""
    state = orchestrator.get_train_state(train_number)
    if not state:
        raise HTTPException(
            status_code=404, detail=f"No active state found for train '{train_number}'."
        )
    return state.model_dump()


@router.get("/journeys/{journey_id}")

def get_journey_state(journey_id: str):
    """Returns active passenger journey status."""
    journey = orchestrator.get_journey_state(journey_id)
    if not journey:
        raise HTTPException(
            status_code=404, detail=f"No active journey found with ID '{journey_id}'."
        )
    return journey.model_dump()


@router.get("/eta/{train_number}/{station_code}")

def get_dynamic_eta(
    train_number: str, station_code: str, scheduled_arrival: str = Query(...)
):
    """Computes dynamic ETA for a train at a specific station."""
    result = orchestrator.calculate_dynamic_eta(
        train_number=train_number,
        target_station=station_code,
        scheduled_arrival_iso=scheduled_arrival,
    )
    return result.model_dump()


@router.get("/incidents")

def list_incidents():
    """Lists all active operational incidents."""
    incidents = orchestrator.incident_engine.get_active_incidents()
    return {"incidents": [inc.model_dump() for inc in incidents]}


@router.post("/notifications/dispatch", status_code=200)

def manual_dispatch_notification(req: DispatchNotificationRequest):
    """Dispatches a manual or operational notification to a passenger."""
    journey = orchestrator.get_journey_state(req.journey_id)
    if not journey:
        raise HTTPException(
            status_code=404, detail=f"Journey ID '{req.journey_id}' not found."
        )

    from app.realtime.models import Incident
    from app.realtime.interfaces import IncidentSeverity
    from datetime import datetime, timezone

    dummy_inc = Incident(
        incident_id="manual-advisory",
        train_number=journey.train_number,
        severity=IncidentSeverity.MEDIUM,
        title=req.title,
        description=req.message,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    notification = orchestrator.notification_engine.orchestrate_notification(
        journey=journey, incident=dummy_inc, custom_message=req.message
    )
    return {"status": "DISPATCHED", "notification": notification.model_dump()}


@router.get("/dashboard")

def get_dashboard():
    """Returns control room operational metrics."""
    return orchestrator.get_dashboard_metrics().model_dump()


@router.get("/ai-context/{train_number}")

def get_ai_context(train_number: str, journey_id: Optional[str] = None):
    """Provides live operational context for AI Core and recommendation engines."""
    ctx = orchestrator.get_live_ai_context(
        train_number=train_number, journey_id=journey_id
    )
    return ctx.model_dump()


@router.get("/health")

def realtime_health():
    """Health check for Real-Time Operations Platform."""
    metrics = orchestrator.observability.get_metrics_snapshot()
    return {"status": "UP", "platform": "Real-Time Operations", "telemetry": metrics}
