"""
Enterprise Configuration Management for Milestone 6.5 AI Memory Platform.
Provides centralized configuration parameters for memory lifecycles, consent enforcement,
and quality score thresholds.
"""

from dataclasses import dataclass, field
import os


@dataclass(frozen=True)
class MemoryConfig:
    """Centralized configuration properties for the AI Memory Platform."""

    # Lifecycle retention policy defaults
    idle_expiration_days: int = field(
        default_factory=lambda: int(os.getenv("MEMORY_IDLE_EXPIRATION_DAYS", "365"))
    )
    max_age_days: int = field(
        default_factory=lambda: int(os.getenv("MEMORY_MAX_AGE_DAYS", "730"))
    )
    saga_max_retention_days: int = field(
        default_factory=lambda: int(os.getenv("MEMORY_SAGA_MAX_RETENTION_DAYS", "7"))
    )

    # Privacy & Consent Settings
    enforce_explicit_opt_in: bool = field(
        default_factory=lambda: (
            os.getenv("MEMORY_ENFORCE_EXPLICIT_OPT_IN", "true").lower() == "true"
        )
    )
    auto_purge_on_consent_withdraw: bool = field(
        default_factory=lambda: (
            os.getenv("MEMORY_AUTO_PURGE_ON_WITHDRAW", "true").lower() == "true"
        )
    )

    # Observability & Audit Settings
    immutable_audit_logging_enabled: bool = field(
        default_factory=lambda: (
            os.getenv("MEMORY_AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        )
    )

    # Memory Quality Score Thresholds
    min_quality_score_threshold: float = field(
        default_factory=lambda: float(os.getenv("MEMORY_MIN_QUALITY_THRESHOLD", "0.50"))
    )


# Singleton configuration instance
default_memory_config = MemoryConfig()
