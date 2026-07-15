# app/journey/audit/logger.py
import logging
from typing import Dict, Any
from app.journey.interfaces.contracts import IAuditEngine
from app.journey.repositories.interfaces import IAuditRepository

logger = logging.getLogger("ai-service.journey.audit")


class AuditEngine(IAuditEngine):
    def __init__(self, repository: IAuditRepository = None):
        self.repository = repository

    async def write_audit_record(
        self,
        decision_id: str,
        recommendation_id: str,
        correlation_id: str,
        data: Dict[str, Any],
    ) -> None:
        payload = {
            "decision_id": decision_id,
            "recommendation_id": recommendation_id,
            "correlation_id": correlation_id,
            "audit_data": data,
        }

        # Log to structured loggers
        logger.info(
            f"AUDIT_RECORD:{decision_id} [Correlation: {correlation_id}] details: {payload}"
        )

        # Persist if repository exists
        if self.repository:
            await self.repository.save_audit(decision_id, payload)
