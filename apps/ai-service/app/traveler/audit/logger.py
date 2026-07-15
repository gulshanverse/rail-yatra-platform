# app/traveler/audit/logger.py
import logging
from typing import Any
from app.traveler.interfaces.contracts import IAuditEngine
from app.traveler.dto.models import TravelerAuditDTO

logger = logging.getLogger("ai-service.traveler.audit")


class AuditEngine(IAuditEngine):
    def __init__(self, repository: Any = None):
        self.repository = repository

    async def log_guidance(self, audit: TravelerAuditDTO) -> None:
        payload = audit.model_dump()
        logger.info(f"AUDIT_RECORD_TRAVELER:{audit.audit_record_id} details: {payload}")
        if self.repository:
            await self.repository.save_audit(audit.audit_record_id, payload)
