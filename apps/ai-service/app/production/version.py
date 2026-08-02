"""
Production Platform Version Information.
"""

import platform
import sys
from datetime import datetime, timezone


BUILD_VERSION = "10.0.0"
BUILD_PHASE = "Phase 10 – Production Platform & Launch Readiness"
BUILD_DATE = "2026-07-31"
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
PLATFORM = platform.system()


def get_version_info() -> dict:
    """Returns structured version and build metadata."""
    return {
        "application": "RailYatra AI Platform",
        "version": BUILD_VERSION,
        "phase": BUILD_PHASE,
        "build_date": BUILD_DATE,
        "python_version": PYTHON_VERSION,
        "platform": PLATFORM,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
