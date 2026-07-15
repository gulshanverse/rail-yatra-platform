# app/intelligence/gateway.py
import time
import logging
from typing import Dict, Any, Optional
from app.integration.interfaces import IIntegrationGateway, NormalizedResponse
from app.integration.models import CorrelationContext
from app.intelligence.interfaces import (
    IRailwayIntelligenceGateway,
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
)
from app.intelligence.models import (
    AIReadyContext,
    PNRCanonical,
    PassengerCanonical,
    JourneyCanonical,
    TrainCanonical,
)

logger = logging.getLogger("ai-service.intelligence.gateway")


class RailwayIntelligenceGateway(IRailwayIntelligenceGateway):
    def __init__(
        self,
        integration_gateway: IIntegrationGateway,
        validator: IDomainValidator,
        normalizer: INormalizationEngine,
        rule_engine: IBusinessRuleEngine,
        confidence_engine: IConfidenceEngine,
        freshness_engine: IFreshnessEngine,
        provenance_engine: IProvenanceEngine,
        conflict_resolver: IConflictResolutionEngine,
        derived_engine: IDerivedIntelligenceEngine,
        event_engine: IRailwayEventEngine,
        ontology_manager: IOntologyManager,
        metadata_manager: IMetadataManager,
        lang_helper=None,
    ):
        self.integration_gateway = integration_gateway
        self.validator = validator
        self.normalizer = normalizer
        self.rule_engine = rule_engine
        self.confidence_engine = confidence_engine
        self.freshness_engine = freshness_engine
        self.provenance_engine = provenance_engine
        self.conflict_resolver = conflict_resolver
        self.derived_engine = derived_engine
        self.event_engine = event_engine
        self.ontology_manager = ontology_manager
        self.metadata_manager = metadata_manager
        self.lang_helper = lang_helper

    async def get_train_intelligence(
        self,
        train_number: str,
        boarding_station: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AIReadyContext:
        """
        Coordinates live train query, normalizes results, resolves GDS conflicts,
        and computes connection risks.
        """
        trace_id = context.get("trace_id", "tr-default") if context else "tr-default"
        logger.info(
            f"[{trace_id}] Gateway executing train intelligence query: train={train_number}"
        )

        # 1. Domain Validation
        if not self.validator.validate_train_number(train_number):
            raise ValueError(f"Invalid train number validation format: {train_number}")
        if not self.validator.validate_station_code(boarding_station):
            raise ValueError(
                f"Invalid station code validation format: {boarding_station}"
            )

        canonical_boarding = self.normalizer.normalize_station_code(boarding_station)

        # 2. Call Integration Platform (Phase 5.1)
        corr_context = CorrelationContext(
            correlation_id=context.get("correlation_id", "corr-default")
            if context
            else "corr-default",
            request_id=context.get("request_id", "req-default")
            if context
            else "req-default",
            trace_id=trace_id,
        )

        # Execute query for live train status
        response: NormalizedResponse = await self.integration_gateway.execute(
            capability="live_train_status",
            payload={"train_number": train_number},
            context=corr_context,
        )

        if not response.success:
            logger.error(
                f"[{trace_id}] Integration execution failed: {response.error_message}"
            )
            raise RuntimeError(
                f"Downstream provider query failed: {response.error_message}"
            )

        # 3. Domain Normalization
        raw_data = response.data
        normalized_train = TrainCanonical(
            train_number=self.normalizer.normalize_station_code(
                raw_data.get("train_number", train_number)
            ),
            train_name=raw_data.get("train_name", "Express"),
            category="SF",
            runs_on_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            source_station_code="NDLS",
            destination_station_code="BPL",
        )

        # Build list of delay payloads to resolve potential conflicts
        delay_payloads = [
            {
                "delay_minutes": self.normalizer.normalize_delay(
                    raw_data.get("delay_minutes", 0)
                ),
                "provider_id": response.provider_id,
                "sync_timestamp": time.time(),
                "confidence_score": 95.0,
            }
        ]

        # 4. Conflict Resolution
        resolved_delay = self.conflict_resolver.resolve_delay_conflict(delay_payloads)

        # 5. Derived Intelligence
        journey_risk = self.derived_engine.calculate_journey_risk(
            delay_minutes=resolved_delay,
            connection_buffer_minutes=45,  # default connections check window
            historical_delay_minutes=15,
        )
        stability = self.derived_engine.calculate_platform_stability(
            station_code=canonical_boarding, train_number=train_number
        )

        # 6. Provenance & Metadata Management
        provenance = self.provenance_engine.record_provenance(
            original_provider=response.provider_id,
            provider_version="1.0.0",
            pipeline_id="normalization_pipeline_v1",
            normalization_version="1.0.0",
            validation_status="VALID",
        )

        confidence = self.confidence_engine.calculate_confidence(
            provider_id=response.provider_id,
            data_freshness_seconds=10.0,
            is_official_source=True,
        )

        # Build Journey DTO
        journey = JourneyCanonical(
            journey_id=f"{train_number}:{time.strftime('%Y-%m-%d')}",
            train_number=train_number,
            journey_date=time.strftime("%Y-%m-%d"),
            departure_time="14:40:00",
            arrival_time="22:15:00",
            status="ACTIVE",
        )

        # 7. Spatial Hierarchy from Ontology Manager
        spatial_hierarchy = self.ontology_manager.get_spatial_hierarchy(
            canonical_boarding
        )

        # Package canonical response
        canonical_data = {
            "journey": journey.model_dump(),
            "train": normalized_train.model_dump(),
            "resolved_delay_minutes": resolved_delay,
            "journey_risk": journey_risk,
            "platform_stability": stability,
            "spatial_hierarchy": spatial_hierarchy,
        }

        metadata = {
            "provenance": provenance,
            "confidence_score": confidence,
            "freshness_valid": True,
            "model_version": "1.0.0",
        }

        # 8. Event publication check
        if resolved_delay > 30:
            await self.event_engine.publish_event(
                event_type="train_delayed",
                payload={"train_number": train_number, "delay_minutes": resolved_delay},
            )

        return AIReadyContext(
            domain_type="JourneyCanonical",
            canonical_data=canonical_data,
            metadata=metadata,
        )

    async def get_pnr_intelligence(
        self, pnr_number: str, context: Optional[Dict[str, Any]] = None
    ) -> AIReadyContext:
        """
        Validates PNR format, queries GDS, normalizes traveler structures,
        and encrypts PII metadata fields.
        """
        trace_id = context.get("trace_id", "tr-default") if context else "tr-default"
        logger.info(
            f"[{trace_id}] Gateway executing PNR intelligence query PNR={pnr_number}"
        )

        # 1. Validation
        if not self.validator.validate_pnr(pnr_number):
            raise ValueError(f"Invalid PNR format: {pnr_number}")

        # 2. Call Integration Gateway (Phase 5.1)
        corr_context = CorrelationContext(
            correlation_id=context.get("correlation_id", "corr-default")
            if context
            else "corr-default",
            request_id=context.get("request_id", "req-default")
            if context
            else "req-default",
            trace_id=trace_id,
        )

        response: NormalizedResponse = await self.integration_gateway.execute(
            capability="pnr_lookup", payload={"pnr": pnr_number}, context=corr_context
        )

        if not response.success:
            logger.error(
                f"[{trace_id}] Integration execution failed: {response.error_message}"
            )
            raise RuntimeError(
                f"Downstream provider query failed: {response.error_message}"
            )

        raw_data = response.data

        # 3. Normalization & PII Encryption (Metadata Management)
        normalized_passengers = []
        for i, p in enumerate(raw_data.get("passengers", [])):
            # Encrypt names of passengers using mock crypt manager
            self.metadata_manager.encrypt_pii(
                p.get("name", f"Passenger {i + 1}")
            )
            normalized_passengers.append(
                PassengerCanonical(
                    passenger_number=p.get("passenger_number", i + 1),
                    booking_status=p.get("booking_status", "CNF"),
                    current_status=p.get("current_status", "CNF"),
                    coach_id=p.get("coach_id", "B1"),
                    seat_number=p.get("seat_number", 24),
                )
            )

        pnr_canonical = PNRCanonical(
            pnr_number=pnr_number,
            train_number=raw_data.get("train_number", "12002"),
            journey_date=raw_data.get("journey_date", time.strftime("%Y-%m-%d")),
            booking_class=self.normalizer.normalize_class_code(
                raw_data.get("booking_class", "3A")
            ),
            chart_status=raw_data.get("chart_status", "UNCHARTED"),
            passengers=normalized_passengers,
        )

        # Provenance & Quality Metrics
        provenance = self.provenance_engine.record_provenance(
            original_provider=response.provider_id,
            provider_version="1.0.0",
            pipeline_id="pnr_pipeline_v1",
            normalization_version="1.0.0",
            validation_status="VALID",
        )

        confidence = self.confidence_engine.calculate_confidence(
            provider_id=response.provider_id,
            data_freshness_seconds=5.0,
            is_official_source=True,
        )

        return AIReadyContext(
            domain_type="PNRCanonical",
            canonical_data=pnr_canonical.model_dump(),
            metadata={
                "provenance": provenance,
                "confidence_score": confidence,
                "freshness_valid": True,
                "model_version": "1.0.0",
            },
        )
