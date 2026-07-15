# app/intelligence/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IDomainValidator(ABC):
    @abstractmethod
    def validate_train_number(self, train_number: str) -> bool:
        """Verifies if train number string contains exactly 5 digits."""
        pass

    @abstractmethod
    def validate_station_code(self, station_code: str) -> bool:
        """Verifies if station code matches capital alphabetic patterns (3-5 uppercase letters)."""
        pass

    @abstractmethod
    def validate_pnr(self, pnr: str) -> bool:
        """Verifies if PNR matches exactly 10 digits."""
        pass

    @abstractmethod
    def validate_coach_label(self, coach_label: str) -> bool:
        """Verifies if coach label (e.g. S1, A1, B1, M1) is well-formed."""
        pass

    @abstractmethod
    def validate_platform_number(self, platform_number: str) -> bool:
        """Verifies if platform number matches standard alphanumeric format."""
        pass

    @abstractmethod
    def validate_date(self, date_str: str) -> bool:
        """Verifies if travel date is within advanced booking window (120 days)."""
        pass


class INormalizationEngine(ABC):
    @abstractmethod
    def normalize_station_code(self, raw_station: str) -> str:
        """Maps aliases and lowercase station names to canonical uppercase codes."""
        pass

    @abstractmethod
    def normalize_delay(self, raw_delay: Any) -> int:
        """Normalizes time delays to integer minutes."""
        pass

    @abstractmethod
    def normalize_class_code(self, raw_class: str) -> str:
        """Standardizes service class labels (e.g. converting '3AC' or '3-Tier' to '3A')."""
        pass

    @abstractmethod
    def normalize_platform_number(self, raw_platform: Any) -> str:
        """Normalizes platform designation to uppercase alphanumeric (e.g. 'PF-1' to '1')."""
        pass

    @abstractmethod
    def normalize_quota_code(self, raw_quota: str) -> str:
        """Maps quotas (e.g. 'TATKAL' or 'General' to 'TQ' or 'GN')."""
        pass


class IBusinessRuleEngine(ABC):
    @abstractmethod
    def evaluate_refund_policy(
        self,
        cancellation_status: str,
        booking_class: str,
        hours_before_departure: int,
        base_fare: float,
    ) -> float:
        """Calculates exact refund amount based on IR rules."""
        pass

    @abstractmethod
    def is_tatkal_window_active(self, class_type: str, current_time_str: str) -> bool:
        """Checks if Tatkal reservation windows are open based on system time settings."""
        pass


class IConfidenceEngine(ABC):
    @abstractmethod
    def calculate_confidence(
        self, provider_id: str, data_freshness_seconds: float, is_official_source: bool
    ) -> float:
        """Calculates a reliability score (0.0 to 100.0) based on source authority and age decay."""
        pass


class IFreshnessEngine(ABC):
    @abstractmethod
    def is_stale(self, capability: str, data_age_seconds: float) -> bool:
        """Checks if cached records are stale based on configured time limits."""
        pass

    @abstractmethod
    def get_max_age_seconds(self, capability: str) -> float:
        """Gets maximum acceptable age limits in seconds."""
        pass


class IProvenanceEngine(ABC):
    @abstractmethod
    def record_provenance(
        self,
        original_provider: str,
        provider_version: str,
        pipeline_id: str,
        normalization_version: str,
        validation_status: str,
    ) -> Dict[str, Any]:
        """Generates provenance metadata tracing data lineage."""
        pass


class IConflictResolutionEngine(ABC):
    @abstractmethod
    def resolve_delay_conflict(self, delay_payloads: List[Dict[str, Any]]) -> int:
        """Resolves conflicting delay reports by selecting the most reliable source."""
        pass

    @abstractmethod
    def resolve_platform_conflict(self, platform_payloads: List[Dict[str, Any]]) -> str:
        """Resolves conflicting platform assignments."""
        pass


class IDerivedIntelligenceEngine(ABC):
    @abstractmethod
    def calculate_journey_risk(
        self,
        delay_minutes: int,
        connection_buffer_minutes: int,
        historical_delay_minutes: int,
    ) -> str:
        """Calculates journey risk level (LOW, MEDIUM, HIGH) for connecting journeys."""
        pass

    @abstractmethod
    def calculate_platform_stability(
        self, station_code: str, train_number: str
    ) -> float:
        """Calculates probability of platform assignment changes based on history."""
        pass


class IRailwayEventEngine(ABC):
    @abstractmethod
    async def publish_event(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publishes canonical events (e.g. 'PLATFORM_CHANGED') to message brokers."""
        pass


class IOntologyManager(ABC):
    @abstractmethod
    def get_zone_for_division(self, division_code: str) -> str:
        """Resolves zone code from a division code."""
        pass

    @abstractmethod
    def get_division_for_station(self, station_code: str) -> str:
        """Resolves administrative division from a station code."""
        pass

    @abstractmethod
    def get_spatial_hierarchy(self, station_code: str) -> Dict[str, Any]:
        """Builds a spatial mapping path from Network down to Station Platform."""
        pass


class IMetadataManager(ABC):
    @abstractmethod
    def encrypt_pii(self, plaintext: str) -> str:
        """AES-256 Mock encryption of sensitive passenger elements."""
        pass

    @abstractmethod
    def decrypt_pii(self, ciphertext: str) -> str:
        """Decrypts encrypted metadata fields."""
        pass


class IRailwayIntelligenceGateway(ABC):
    @abstractmethod
    async def get_train_intelligence(
        self,
        train_number: str,
        boarding_station: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Coordinates validation, queries the 5.1 integration gateway, normalizes outputs,
        resolves conflicts, adds derived metrics, and returns the canonical context.
        """
        pass

    @abstractmethod
    async def get_pnr_intelligence(
        self, pnr_number: str, context: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Validates PNR format, queries GDS, normalizes traveler structures,
        and encrypts PII metadata fields.
        """
        pass
