# app/booking/config/registry.py
from typing import Dict, Any

# ==========================================
# Feature Flags Config
# ==========================================
FEATURE_FLAGS = {
    "ENABLE_ALT_BOARDING": True,
    "ENABLE_ADVANCED_CONFIRMATION": True,
    "ENABLE_QUOTA_OPTIMIZATION": True,
    "ENABLE_RECOVERY_ENGINE": True,
    "ENABLE_EXPLANATION_V2": True,
    "ENABLE_DYNAMIC_STRATEGY": True,
}

# ==========================================
# Policy Configurations Registry
# ==========================================
POLICY_REGISTRY = {
    "Availability": {
        "ttl_snapshot_seconds": 300,
        "stale_threshold_seconds": 600,
    },
    "Confirmation": {
        "high_confidence_wl_limit": 10,
        "medium_confidence_wl_limit": 30,
        "min_days_to_departure": 3,
    },
    "Quota": {"priority_order": ["HP", "SS", "LD", "DF", "GN", "TQ", "PT"]},
    "Boarding": {
        "max_boarding_offset_km": 100,
        "cost_overhead_pct": 0.25,
    },
    "Risk": {
        "critical_risk_probability": 0.40,
        "connection_safety_margin_minutes": 20,
    },
    "Scoring": {
        "default_weights": {
            "confirmation": 0.40,
            "cost": 0.30,
            "comfort": 0.20,
            "time": 0.10,
        }
    },
}


def is_feature_enabled(flag_name: str) -> bool:
    return FEATURE_FLAGS.get(flag_name, False)


def get_policy(policy_name: str) -> Dict[str, Any]:
    return POLICY_REGISTRY.get(policy_name, {})
