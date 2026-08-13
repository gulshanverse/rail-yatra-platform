"""
Production Router – Exposes production endpoints for health, readiness, liveness, metrics, diagnostics, backup/restore, security, and recovery.
"""

from typing import Dict, Any, List
from fastapi import APIRouter, Response

from app.production.version import get_version_info
from app.production.config import production_config
from app.production.health import health_checker
from app.production.readiness import readiness_probe
from app.production.liveness import liveness_probe
from app.production.metrics import metrics_collector
from app.production.diagnostics import diagnostics_engine
from app.production.security import security_manager
from app.production.backup import backup_manager
from app.production.restore import restore_manager
from app.production.recovery import recovery_manager
from app.production.maintenance import maintenance_scheduler

router = APIRouter(tags=["Production Platform & Launch Readiness"])


@router.get("/health", response_model=Dict[str, Any])
def get_health() -> Dict[str, Any]:
    """GET /health - Aggregated operational health with dependency status."""
    return health_checker.check_all()


@router.get("/health/ready", response_model=Dict[str, Any])
def get_readiness() -> Dict[str, Any]:
    """GET /health/ready - Readiness probe for container orchestration."""
    return readiness_probe.check()


@router.get("/health/live", response_model=Dict[str, Any])
def get_liveness() -> Dict[str, Any]:
    """GET /health/live - Liveness probe confirming service process is alive."""
    return liveness_probe.check()


@router.get("/metrics")
def get_metrics(format: str = "prometheus") -> Any:
    """GET /metrics - Application, system, and dependency telemetry metrics."""
    if format == "json":
        return metrics_collector.get_metrics()
    return Response(content=metrics_collector.prometheus_text(), media_type="text/plain")


@router.get("/version", response_model=Dict[str, Any])
def get_version() -> Dict[str, Any]:
    """GET /version - Build version, phase, and environment details."""
    return get_version_info()


@router.get("/diagnostics", response_model=Dict[str, Any])
def get_diagnostics() -> Dict[str, Any]:
    """GET /diagnostics - Runtime diagnostics and configuration status."""
    return diagnostics_engine.collect()


@router.get("/production/config", response_model=Dict[str, Any])
def get_production_configuration() -> Dict[str, Any]:
    """GET /production/config - Safe production configuration summary."""
    return production_config.to_dict()


@router.get("/production/security", response_model=Dict[str, Any])
def get_security_status() -> Dict[str, Any]:
    """GET /production/security - Security hardening and header status."""
    return security_manager.validate_configuration()


@router.post("/production/backup", response_model=Dict[str, Any])
def trigger_backup(backup_type: str = "DATABASE") -> Dict[str, Any]:
    """POST /production/backup - Triggers a platform backup operation."""
    if backup_type == "CONFIGURATION":
        record = backup_manager.backup_configuration()
    elif backup_type == "METADATA":
        record = backup_manager.backup_metadata()
    else:
        record = backup_manager.backup_database()
    return record.to_dict()


@router.get("/production/backups", response_model=List[Dict[str, Any]])
def list_backups() -> List[Dict[str, Any]]:
    """GET /production/backups - Lists all backup records."""
    return backup_manager.list_backups()


@router.post("/production/restore", response_model=Dict[str, Any])
def trigger_restore(backup_id: str, target: str = "postgresql") -> Dict[str, Any]:
    """POST /production/restore - Triggers a restore operation from a backup."""
    record = restore_manager.execute_restore(backup_id, target)
    return record.to_dict()


@router.get("/production/recovery", response_model=Dict[str, Any])
def get_disaster_recovery_status() -> Dict[str, Any]:
    """GET /production/recovery - Disaster recovery procedures and status."""
    return recovery_manager.get_recovery_status()


@router.get("/production/maintenance", response_model=Dict[str, Any])
def get_maintenance_status() -> Dict[str, Any]:
    """GET /production/maintenance - Scheduled background maintenance tasks."""
    return maintenance_scheduler.get_summary()


@router.get("/test-gemini")
async def test_gemini_direct(model: str = "gemini-3.5-flash"):
    import os
    google_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not google_key:
        return {"ok": False, "error": "No GOOGLE_API_KEY found in env"}

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        llm = ChatGoogleGenerativeAI(google_api_key=google_key, model=model)
        res = await llm.ainvoke([HumanMessage(content="Reply with exactly: GEMINI_ONLINE_OK")])
        from app.agents.base import extract_text_content
        return {"ok": True, "reply": extract_text_content(res.content), "model": model}
    except Exception as e:
        return {"ok": False, "error": str(e), "type": type(e).__name__, "tested_model": model}


