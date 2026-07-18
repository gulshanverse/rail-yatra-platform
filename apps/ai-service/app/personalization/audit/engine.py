# app/personalization/audit/engine.py
import logging
from app.personalization.interfaces.contracts import IAuditEngine, IAuditRepository
from app.personalization.dto.models import PreferenceAuditDTO

logger = logging.getLogger(__name__)


class AuditEngine(IAuditEngine):
    def __init__(self, audit_repository: IAuditRepository) -> None:
        self._audit_repo = audit_repository

    def log(self, audit: PreferenceAuditDTO) -> str:
        logger.info("Logging preference audit record audit_id=%s", audit.audit_id)
        self._audit_repo.save(audit)
        return audit.audit_id

    def verify(self, audit_id: str) -> bool:
        logger.info("Verifying preference audit record audit_id=%s", audit_id)
        record = self._audit_repo.get_by_id(audit_id)
        if record is None:
            logger.warning(
                "Audit record not found for verification audit_id=%s", audit_id
            )
            return False
        # Simulating cryptographic verification of the hash signature
        return (
            record.cryptographic_hash is not None and len(record.cryptographic_hash) > 0
        )
