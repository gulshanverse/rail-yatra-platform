# app/intelligence/__init__.py
from app.intelligence.interfaces import (
    IDomainValidator,
    INormalizationEngine,
    IBusinessRuleEngine,
    IConfidenceEngine,
    IFreshnessEngine,
    IProvenanceEngine,
    IConflictResolutionEngine,
    IDerivedIntelligenceEngine,
    IRailwayEventEngine,
    IOntologyManager,
    IMetadataManager,
    IRailwayIntelligenceGateway,
)
from app.intelligence.models import (
    CanonicalMetadata,
    ProvenanceMetadata,
    StationCanonical,
    TrainCanonical,
    JourneyCanonical,
    PassengerCanonical,
    PNRCanonical,
    CoachCanonical,
    PlatformCanonical,
    QuotaCanonical,
    FareCanonical,
    DelayCanonical,
    CancellationCanonical,
    AlertCanonical,
    CompositionCanonical,
    TravelEventCanonical,
    AIReadyContext,
)
from app.intelligence.config import intelligence_settings, IntelligenceSettings
from app.intelligence.validator import DomainValidator
from app.intelligence.normalizer import NormalizationEngine
from app.intelligence.rules import BusinessRuleEngine
from app.intelligence.confidence import ConfidenceEngine
from app.intelligence.freshness import FreshnessEngine
from app.intelligence.provenance import ProvenanceEngine
from app.intelligence.conflict import ConflictResolutionEngine
from app.intelligence.derived import DerivedIntelligenceEngine
from app.intelligence.events import RailwayEventEngine
from app.intelligence.ontology import OntologyManager
from app.intelligence.metadata import MetadataManager
from app.intelligence.lang import LanguageManager
from app.intelligence.gateway import RailwayIntelligenceGateway

__all__ = [
    # Interfaces
    "IDomainValidator",
    "INormalizationEngine",
    "IBusinessRuleEngine",
    "IConfidenceEngine",
    "IFreshnessEngine",
    "IProvenanceEngine",
    "IConflictResolutionEngine",
    "IDerivedIntelligenceEngine",
    "IRailwayEventEngine",
    "IOntologyManager",
    "IMetadataManager",
    "IRailwayIntelligenceGateway",
    # Models
    "CanonicalMetadata",
    "ProvenanceMetadata",
    "StationCanonical",
    "TrainCanonical",
    "JourneyCanonical",
    "PassengerCanonical",
    "PNRCanonical",
    "CoachCanonical",
    "PlatformCanonical",
    "QuotaCanonical",
    "FareCanonical",
    "DelayCanonical",
    "CancellationCanonical",
    "AlertCanonical",
    "CompositionCanonical",
    "TravelEventCanonical",
    "AIReadyContext",
    # Implementations
    "intelligence_settings",
    "IntelligenceSettings",
    "DomainValidator",
    "NormalizationEngine",
    "BusinessRuleEngine",
    "ConfidenceEngine",
    "FreshnessEngine",
    "ProvenanceEngine",
    "ConflictResolutionEngine",
    "DerivedIntelligenceEngine",
    "RailwayEventEngine",
    "OntologyManager",
    "MetadataManager",
    "LanguageManager",
    "RailwayIntelligenceGateway",
]
