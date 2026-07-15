# app/traveler/config/registry.py
from typing import Dict, Any

FEATURE_FLAGS = {
    "ENABLE_RECOVERY_ENGINE": True,
    "ENABLE_SMOOTH_TIMELINE": True,
    "ENABLE_ADVANCED_GUIDANCE": True,
    "ENABLE_ALERT_SUPPRESSION": True,
    "ENABLE_PRIORITY_ESCALATION": True,
    "ENABLE_DYNAMIC_REMINDERS": True,
    "ENABLE_CONTEXT_RECALCULATION": True,
}

POLICY_REGISTRY: Dict[str, Any] = {
    "Alert": {
        "deduplication_delta_minutes": 10,
    },
    "Reminder": {
        "departure_offset_hours": 2.0,
        "boarding_offset_minutes": 20,
        "arrival_offset_minutes": 15,
    },
    "Priority": {
        "EMERGENCY": {"escalation_timeout_sec": 60, "can_suppress": False},
        "CRITICAL": {"escalation_timeout_sec": 180, "can_suppress": False},
        "HIGH": {"escalation_timeout_sec": 300, "can_suppress": True},
        "MEDIUM": {"escalation_timeout_sec": 600, "can_suppress": True},
        "LOW": {"escalation_timeout_sec": 0, "can_suppress": True},
    },
}


def is_feature_enabled(flag: str) -> bool:
    return FEATURE_FLAGS.get(flag, False)


def get_policy(policy_name: str) -> Dict[str, Any]:
    result = POLICY_REGISTRY.get(policy_name)
    if result is None:
        return {}
    return result
