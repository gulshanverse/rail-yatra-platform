# app/personalization/validators/context.py
from app.personalization.interfaces.contracts import IContextValidator
from app.personalization.dto.models import TravelerPersonalizationContext


class ContextValidator(IContextValidator):
    def validate_context(self, context: TravelerPersonalizationContext) -> bool:
        if not context:
            return False
        if not context.traveler_id:
            return False
        if not context.correlation_id:
            return False
        if context.version < 0:
            return False
        return True
