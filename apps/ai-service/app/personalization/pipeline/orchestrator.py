# app/personalization/pipeline/orchestrator.py
from datetime import datetime
import logging
import hashlib
import uuid
from typing import Dict, Any
from app.personalization.interfaces.contracts import (
    IPipelineOrchestrator,
    IRecommendationAdaptationEngine,
    IReasonCodeEngine,
    IExplanationEngine,
    IAuditEngine,
    IMetricsEngine,
)
from app.personalization.dto.models import (
    TravelerPersonalizationContext,
    AIReadyPersonalizationContext,
    PreferenceEvidenceDTO,
    PreferenceAuditDTO,
)

logger = logging.getLogger(__name__)


class PipelineOrchestrator(IPipelineOrchestrator):
    def __init__(
        self,
        adaptation_engine: IRecommendationAdaptationEngine,
        reason_code_engine: IReasonCodeEngine,
        explanation_engine: IExplanationEngine,
        audit_engine: IAuditEngine,
        metrics_engine: IMetricsEngine,
    ) -> None:
        self._adaptation_engine = adaptation_engine
        self._reason_code_engine = reason_code_engine
        self._explanation_engine = explanation_engine
        self._audit_engine = audit_engine
        self._metrics_engine = metrics_engine

    async def execute(
        self,
        context: TravelerPersonalizationContext,
        raw_dto: Dict[str, Any],
    ) -> AIReadyPersonalizationContext:
        traveler_id = context.traveler_id
        scenario = raw_dto.get("scenario", "JOURNEY_LISTING")
        logger.info("Executing pipeline orchestrator for traveler=%s", traveler_id)

        try:
            # 1. Adaptation
            adaptation = self._adaptation_engine.adapt(raw_dto, context)

            # 2. Get reason code
            reason_code_dto = self._reason_code_engine.lookup(adaptation.reason_code)

            # 3. Create evidence
            evidence = PreferenceEvidenceDTO(
                evidence_id=f"ev-{uuid.uuid4().hex[:12]}",
                preference_id=f"pref-{uuid.uuid4().hex[:12]}",
                observation_ids=context.evidence_references.get(
                    adaptation.reason_code, []
                ),
                rule_triggers=[],
                timestamp=datetime.utcnow(),
            )

            # 4. Generate explanation
            explanation_dict = self._explanation_engine.explain(
                reason_code_dto, evidence, "en-US"
            )

            # 5. Audit log
            hash_input = f"{context.traveler_id}:{adaptation.reason_code}:{datetime.utcnow().isoformat()}"
            sig_hash = hashlib.sha256(hash_input.encode("utf-8")).hexdigest()

            audit = PreferenceAuditDTO(
                audit_id=f"aud-{uuid.uuid4().hex[:12]}",
                correlation_id=context.correlation_id,
                timestamp=datetime.utcnow(),
                traveler_id=traveler_id,
                action="PREFERENCE_APPLIED",
                change_log={
                    "scenario": scenario,
                    "adapted_fields": adaptation.adapted_fields,
                    "reason_code": adaptation.reason_code,
                },
                policy_applied="explainability_policy",
                cryptographic_hash=sig_hash,
            )
            self._audit_engine.log(audit)

            # 6. Metrics
            self._metrics_engine.increment(
                "personalization.executed", {"scenario": scenario}
            )

            return AIReadyPersonalizationContext(
                personalization_context_id=f"ctx-{uuid.uuid4().hex[:12]}",
                context=context,
                explanations=[explanation_dict],
                audit_token=audit.audit_id,
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(
                "Personalization pipeline failed for traveler=%s: %s",
                traveler_id,
                e,
                exc_info=True,
            )
            self._metrics_engine.increment(
                "personalization.failed", {"scenario": scenario}
            )

            empty_audit_id = f"aud-fallback-{uuid.uuid4().hex[:8]}"
            fallback_audit = PreferenceAuditDTO(
                audit_id=empty_audit_id,
                correlation_id=context.correlation_id,
                timestamp=datetime.utcnow(),
                traveler_id=traveler_id,
                action="FALLBACK_APPLIED",
                change_log={"error": str(e)},
                policy_applied="fallback_policy",
                cryptographic_hash="fallback-sig",
            )
            try:
                self._audit_engine.log(fallback_audit)
            except Exception:
                pass

            return AIReadyPersonalizationContext(
                personalization_context_id=f"ctx-fallback-{uuid.uuid4().hex[:8]}",
                context=context,
                explanations=[
                    {
                        "explanation": "Default settings applied.",
                        "locale": "en-US",
                        "reason_code": "PREF_DEFAULT",
                        "evidence_id": "fallback",
                    }
                ],
                audit_token=empty_audit_id,
                timestamp=datetime.utcnow(),
            )
