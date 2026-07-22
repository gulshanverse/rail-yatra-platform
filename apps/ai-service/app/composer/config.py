"""
Enterprise Configuration Management for Milestone 6.6 AI Response Composer & Explainability Platform.
Provides configuration parameters for synthesis latency budgets, confidence thresholds,
progressive disclosure, and DPDP privacy guardrails.
"""

from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class ComposerConfig:
    """Centralized configuration properties for the AI Response Composer Platform."""

    # Latency & Performance Budget (ms)
    max_composition_latency_ms: float = field(
        default_factory=lambda: float(os.getenv("COMPOSER_MAX_LATENCY_MS", "150.0"))
    )

    # Privacy & DPDP Settings
    enforce_consent_before_personalization: bool = field(
        default_factory=lambda: (
            os.getenv("COMPOSER_ENFORCE_CONSENT", "true").lower() == "true"
        )
    )
    pii_masking_enabled: bool = field(
        default_factory=lambda: (
            os.getenv("COMPOSER_PII_MASKING_ENABLED", "true").lower() == "true"
        )
    )

    # Progressive Disclosure & Scannability
    enable_progressive_disclosure: bool = field(
        default_factory=lambda: (
            os.getenv("COMPOSER_PROGRESSIVE_DISCLOSURE", "true").lower() == "true"
        )
    )
    max_action_chips: int = field(
        default_factory=lambda: int(os.getenv("COMPOSER_MAX_ACTION_CHIPS", "3"))
    )
    max_follow_up_suggestions: int = field(
        default_factory=lambda: int(
            os.getenv("COMPOSER_MAX_FOLLOW_UPS", "3")
        )
    )

    # Confidence Thresholds
    min_confidence_for_direct_assertion: float = field(
        default_factory=lambda: float(
            os.getenv("COMPOSER_HIGH_CONFIDENCE_THRESHOLD", "0.85")
        )
    )
    low_confidence_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("COMPOSER_LOW_CONFIDENCE_THRESHOLD", "0.60")
        )
    )
    uncertain_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("COMPOSER_UNCERTAIN_THRESHOLD", "0.30")
        )
    )

    # Governance & Audit Settings
    immutable_audit_logging_enabled: bool = field(
        default_factory=lambda: (
            os.getenv("COMPOSER_AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        )
    )
    min_quality_score_threshold: float = field(
        default_factory=lambda: float(
            os.getenv("COMPOSER_MIN_QUALITY_THRESHOLD", "0.80")
        )
    )


# Singleton configuration instance
default_composer_config = ComposerConfig()
