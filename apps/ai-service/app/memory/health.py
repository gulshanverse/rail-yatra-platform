"""
Health Monitor, Health Routing, and Observability Metrics.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Response, status

from app.memory.healing import healing_metrics, circuit_breaker
from app.memory.recovery import RecoveryAuditTrail

logger = logging.getLogger("ai-service.memory.health")

router = APIRouter()

# Global metrics tracking health transitions and execution logs
health_metrics_store: Dict[str, Any] = {
    "redis_reconnect_count": 0,
    "worker_uptime_seconds": 0,
    "worker_restart_count": 0,
    "lock_cleanup_count": 0,
    "session_cleanup_count": 0,
    "memory_synchronization_count": 0,
    "recovery_attempts": 0,
    "recovery_successes": 0,
    "recovery_failures": 0,
    "average_recovery_latency_ms": 0.0,
    "health_transitions": 0,
    "last_state": "HEALTHY",
}


class HealthMonitor:
    """Enterprise Health Monitoring returning states: HEALTHY, DEGRADED, RECOVERING, UNAVAILABLE."""

    def __init__(self) -> None:
        self.state = "HEALTHY"

    def evaluate_status(self) -> Dict[str, Any]:
        """Assess overall connectivity, fallback usage, and worker counts."""
        from app.memory.short_term import short_term_memory
        redis_up = False
        if short_term_memory.redis_client:
            try:
                circuit_breaker.execute(short_term_memory.redis_client.ping)
                redis_up = True
            except Exception:
                redis_up = False

        # Determine status state
        cb_state = circuit_breaker.state
        new_state = "HEALTHY"

        if not redis_up:
            if cb_state == "OPEN":
                new_state = "DEGRADED"
            else:
                new_state = "RECOVERING"
        else:
            new_state = "HEALTHY"

        # Track transitions
        if new_state != health_metrics_store["last_state"]:
            health_metrics_store["health_transitions"] += 1
            health_metrics_store["last_state"] = new_state
            logger.warning(f"Health Transition: System state shifted to {new_state}")

        self.state = new_state

        return {
            "status": self.state,
            "circuit_breaker": cb_state,
            "dependencies": {
                "redis": "healthy" if redis_up else "offline",
                "in_memory_fallback": "active"
                if self.state == "DEGRADED"
                else "standby",
            },
        }


monitor = HealthMonitor()

# ----------------- FastAPI Routes -----------------


@router.get("/health")
def health_endpoint():
    status_info = monitor.evaluate_status()
    return {
        "status": status_info["status"],
        "service": "ai-service",
        "version": "1.0.0",
        "dependencies": status_info["dependencies"],
    }


@router.get("/live")
def live_check():
    """Liveness probe returning success if service runs."""
    return {"status": "alive"}


@router.get("/ready")
def ready_check(response: Response):
    """Readiness probe returning 503 if unavailable."""
    status_info = monitor.evaluate_status()
    if status_info["status"] == "UNAVAILABLE":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unready", "details": status_info}
    return {"status": "ready", "details": status_info}


@router.get("/startup")
def startup_check():
    """Startup probe verifying initial initialization."""
    return {"status": "started"}


@router.get("/metrics")
def prometheus_metrics():
    """Export observability data in Prometheus format."""
    status_info = monitor.evaluate_status()

    # Extract audit trails statistics
    trail = RecoveryAuditTrail.get_trail()
    attempts = len(trail)
    successes = sum(1 for e in trail if e["success"])
    failures = attempts - successes
    avg_latency = sum(e["duration_ms"] for e in trail) / max(attempts, 1)

    metrics = [
        "# HELP memory_health_status Overall platform health status (1=Healthy, 2=Degraded, 3=Recovering, 4=Unavailable)"
    ]
    status_val = {"HEALTHY": 1, "DEGRADED": 2, "RECOVERING": 3, "UNAVAILABLE": 4}.get(
        status_info["status"], 4
    )
    metrics.append(f"memory_health_status {status_val}")

    metrics.extend(
        [
            "# HELP memory_recovery_attempts_total Total recovery attempts initiated",
            f"memory_recovery_attempts_total {attempts}",
            "# HELP memory_recovery_success_total Total successful recovery operations",
            f"memory_recovery_success_total {successes}",
            "# HELP memory_recovery_failures_total Total failed recovery operations",
            f"memory_recovery_failures_total {failures}",
            "# HELP memory_average_recovery_latency_ms Average recovery time in milliseconds",
            f"memory_average_recovery_latency_ms {avg_latency}",
            "# HELP memory_redis_reconnect_total Reconnections back to Redis client",
            f"memory_redis_reconnect_total {health_metrics_store['redis_reconnect_count']}",
            "# HELP memory_lock_cleanup_total Total locks swept by background worker",
            f"memory_lock_cleanup_total {health_metrics_store['lock_cleanup_count']}",
            "# HELP memory_session_cleanup_total Total sessions evicted by cleanup worker",
            f"memory_session_cleanup_total {health_metrics_store['session_cleanup_count']}",
            "# HELP memory_health_transitions_total Total health status state transitions",
            f"memory_health_transitions_total {health_metrics_store['health_transitions']}",
            "# HELP memory_circuit_breaker_trips_total Total circuit breaker state trips",
            f"memory_circuit_breaker_trips_total {healing_metrics['circuit_breaker_trips']}",
        ]
    )

    return Response(content="\n".join(metrics) + "\n", media_type="text/plain")


@router.get("/recovery/status")
def recovery_status():
    """Retrieve full audit log list and recovery policies state."""
    return {
        "status": monitor.evaluate_status()["status"],
        "audit_trail": RecoveryAuditTrail.get_trail(),
        "healing_metrics": healing_metrics,
    }


@router.get("/workers/status")
def workers_status():
    """Retrieve background worker registration details and logs."""
    from app.memory.workers import supervisor

    return supervisor.get_workers_status()


@router.get("/session/status")
def session_status(session_id: str):
    """Query current session status info (version, fallback status, lock owners)."""
    from app.memory.short_term import short_term_memory
    from app.memory.locks import in_memory_locks_registry

    in_local = short_term_memory.fallback_store.exists(session_id)
    lock_active = session_id in in_memory_locks_registry

    # Get local version if exists
    local_version = None
    if in_local:
        try:
            import json

            meta_json = short_term_memory.fallback_store.get_meta(session_id)
            if meta_json:
                meta_data = json.loads(meta_json)
                local_version = meta_data.get("memory_version")
        except Exception:
            pass

    return {
        "session_id": session_id,
        "active_in_local": in_local,
        "is_locked_locally": lock_active,
        "local_version": local_version,
    }
