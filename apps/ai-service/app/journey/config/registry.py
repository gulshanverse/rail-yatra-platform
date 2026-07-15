# app/journey/config/registry.py
from typing import Dict, Any

# ==========================================
# Feature Flags Config
# ==========================================
FEATURE_FLAGS = {
    "FF_ENABLE_EXPERIMENTAL_RANKING": False,
    "FF_ENABLE_NEW_STRATEGY": True,
    "FF_ENABLE_AI_EXPLANATION": True,
    "FF_ENABLE_DYNAMIC_BUFFER": True,
    "FF_ENABLE_ALTERNATIVE_RANKING": True,
    "FF_ENABLE_EMERGENCY_JOURNEY": True,
    "FF_ENABLE_BETA_RECOMMENDATION": False,
}

# ==========================================
# Policy Configuration Registry
# ==========================================
POLICY_REGISTRY = {
    "Scoring": {
        "weights": {
            "reliability": 0.30,
            "comfort": 0.20,
            "cost": 0.30,
            "duration": 0.20,
        },
        "version": "1.0.0",
        "priority": "High",
    },
    "Risk": {
        "mct_safety_margin_minutes": 20,
        "critical_delay_threshold_minutes": 60,
        "version": "1.0.0",
        "priority": "High",
    },
    "Transfer": {
        "base_walking_speed_mps": 1.2,
        "senior_walking_speed_mps": 0.8,
        "mct_same_platform": 15,
        "mct_cross_platform": 30,
        "mct_terminal_change": 60,
        "version": "1.0.0",
        "priority": "Medium",
    },
    "Cache": {
        "ttl_route_seconds": 86400,
        "ttl_recommendation_seconds": 900,
        "version": "1.0.0",
        "priority": "Medium",
    },
}


def is_feature_enabled(flag_name: str) -> bool:
    return FEATURE_FLAGS.get(flag_name, False)


def get_policy(policy_name: str) -> Dict[str, Any]:
    return POLICY_REGISTRY.get(policy_name, {})
