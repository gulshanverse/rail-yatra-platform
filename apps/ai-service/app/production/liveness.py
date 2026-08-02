"""
Production Liveness Probe – GET /health/live.
Confirms the application process is running and responsive.
"""

from typing import Any, Dict
from datetime import datetime, timezone


class LivenessProbe:
    """Lightweight liveness check confirming the process is alive."""

    def check(self) -> Dict[str, Any]:
        return {
            "alive": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


liveness_probe = LivenessProbe()
