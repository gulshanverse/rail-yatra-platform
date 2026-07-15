# app/booking/audit/logger.py
import logging
from typing import Any
from app.booking.interfaces.contracts import IAuditEngine
from app.booking.dto.models import AuditDTO

logger = logging.getLogger("ai-service.booking.audit")


class AuditEngine(IAuditEngine):
    def __init__(self, repository: Any = None):
        self.repository = repository

    async def log_decision(self, audit: AuditDTO) -> None:
        payload = audit.model_dump()
        logger.info(
            f"AUDIT_RECORD_BOOKING:{audit.booking_decision_id} details: {payload}"
        )
        if self.repository:
            await self.repository.save_audit(audit.booking_decision_id, payload)
