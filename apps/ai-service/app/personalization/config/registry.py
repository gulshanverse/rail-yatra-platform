# app/personalization/config/registry.py
from typing import Dict, Any, Optional

# Compiled Default Values
DEFAULTS: Dict[str, Any] = {
    "preference_policy": {
        "max_active_implicit_preferences": 50,
        "default_expiration_days": 90,
        "allow_implicit_cross_device_sync": True,
    },
    "confidence_policy": {
        "min_confidence_to_apply": 0.70,
        "initial_confidence_weight": 0.50,
        "observation_impact_increment": 0.10,
        "daily_decay_constant": 0.05,
    },
    "learning_policy": {
        "min_observations_for_promotion": 5,
        "max_learning_sessions_per_hour": 60,
        "learning_rule_reload_mode": "DETERMINISTIC_SYNC",
    },
    "conflict_policy": {
        "explicit_always_wins": True,
        "persona_priority_map": {
            "accessibility_needs": 10,
            "business_traveler": 8,
            "weekly_commuter": 7,
            "leisure_family_traveler": 6,
            "budget_seeker": 5,
        },
    },
    "reset_policy": {
        "allow_partial_category_reset": True,
        "retention_after_reset_seconds": 0,
        "backup_before_reset": False,
    },
    "consent_policy": {
        "opt_in_required_for_implicit": True,
        "allow_granular_opt_out": True,
        "consent_reverification_interval_days": 365,
    },
    "retention_policy": {
        "raw_observation_ttl_days": 30,
        "audit_log_retention_days": 1095,
        "inactive_profile_ttl_days": 365,
    },
    "privacy_policy": {
        "encryption_standard": "AES_256_GCM",
        "hash_algorithm": "SHA_256",
        "redact_pii_fields": ["pnr", "mobile", "email", "name"],
    },
    "explainability_policy": {
        "require_evidence_links": True,
        "fallback_template": "Default settings applied.",
    },
    "audit_policy": {
        "immutable_write_retries": 3,
        "require_correlation_id": True,
    },
    "metrics_policy": {
        "collection_interval_seconds": 60,
        "publish_format": "PROMETHEUS_METRICS",
    },
    "health_policy": {
        "heartbeat_interval_seconds": 10,
        "degradation_threshold_ms": 250,
    },
}

# Feature Flags
FEATURE_FLAGS: Dict[str, bool] = {
    "ENABLE_PREFERENCE_LEARNING": True,
    "ENABLE_IMPLICIT_PREFERENCES": True,
    "ENABLE_REASON_CODES": True,
    "ENABLE_ADAPTIVE_RECOMMENDATIONS": True,
    "ENABLE_PERSONALIZED_GUIDANCE": True,
    "ENABLE_CONFLICT_RESOLUTION": True,
    "ENABLE_INHERITANCE_ENGINE": True,
    "ENABLE_EXPLANATION_ENGINE": True,
}


class ConfigurationRegistry:
    def __init__(self) -> None:
        self._configs: Dict[str, Any] = DEFAULTS.copy()
        self._flags: Dict[str, bool] = FEATURE_FLAGS.copy()

    def get_config(self, section: str, key: Optional[str] = None) -> Any:
        section_data = self._configs.get(section)
        if section_data is None:
            return None
        if key is None:
            return section_data
        if isinstance(section_data, dict):
            return section_data.get(key)
        return None

    def set_config(self, section: str, key: str, value: Any) -> None:
        if section not in self._configs:
            self._configs[section] = {}
        if isinstance(self._configs[section], dict):
            self._configs[section][key] = value

    def is_feature_enabled(self, flag_name: str) -> bool:
        return self._flags.get(flag_name, False)

    def set_feature_flag(self, flag_name: str, enabled: bool) -> None:
        self._flags[flag_name] = enabled


# Singleton configuration registry instance
config_registry = ConfigurationRegistry()
