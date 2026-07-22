"""
Feature Flag Framework for Milestone 6.6 AI Response Composer Platform.
Provides dynamic runtime feature toggling, A/B experimentation, and gradual rollout controls.
"""

from typing import Dict
import os


class FeatureFlagRegistry:
    """Centralized feature flag registry supporting environment overrides and runtime toggles."""

    def __init__(self):
        self._flags: Dict[str, bool] = {
            "EXPERIMENTAL_LLM_SYNTHESIS": os.getenv("FLAG_EXPERIMENTAL_LLM_SYNTHESIS", "false").lower() == "true",
            "DEEP_EVIDENCE_EXPLANATIONS": os.getenv("FLAG_DEEP_EVIDENCE_EXPLANATIONS", "true").lower() == "true",
            "PROACTIVE_ACTION_CHIPS": os.getenv("FLAG_PROACTIVE_ACTION_CHIPS", "true").lower() == "true",
            "EMERGENCY_SAFETY_OVERRIDE": os.getenv("FLAG_EMERGENCY_SAFETY_OVERRIDE", "true").lower() == "true",
            "STRICT_DPDP_CONSENT_GATE": os.getenv("FLAG_STRICT_DPDP_CONSENT_GATE", "true").lower() == "true",
            "PII_AUTOMATED_MASKING": os.getenv("FLAG_PII_AUTOMATED_MASKING", "true").lower() == "true",
            "BETA_VOICE_FORMATTER": os.getenv("FLAG_BETA_VOICE_FORMATTER", "false").lower() == "true",
            "MULTI_MODAL_METRO_PLUGIN": os.getenv("FLAG_MULTI_MODAL_METRO_PLUGIN", "false").lower() == "true",
        }

    def is_enabled(self, flag_name: str, default: bool = False) -> bool:
        """Returns whether a feature flag is currently active."""
        return self._flags.get(flag_name.upper(), default)

    def set_flag(self, flag_name: str, enabled: bool) -> None:
        """Dynamically set a flag state at runtime."""
        self._flags[flag_name.upper()] = enabled

    def get_all_flags(self) -> Dict[str, bool]:
        """Returns snapshot of all active feature flags."""
        return dict(self._flags)


# Singleton feature flag registry instance
feature_flags = FeatureFlagRegistry()
