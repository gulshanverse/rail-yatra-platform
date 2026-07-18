# app/personalization/reason_codes/engine.py
import logging
from typing import Dict, Any
from app.personalization.interfaces.contracts import IReasonCodeEngine
from app.personalization.dto.models import ReasonCodeDTO

logger = logging.getLogger(__name__)

PREDEFINED_CODES = {
    "PREF_EXPLICIT_CLASS": ReasonCodeDTO(
        code="PREF_EXPLICIT_CLASS",
        category="COMFORT",
        description="Personalized based on selected class comfort options",
        priority=10,
        explanation_template="Personalized based on your selected comfort class preference of {value}.",
    ),
    "PREF_EXPLICIT_SEAT": ReasonCodeDTO(
        code="PREF_EXPLICIT_SEAT",
        category="COMFORT",
        description="Personalized based on selected seat options",
        priority=9,
        explanation_template="Personalized based on your preferred seat choice of {value}.",
    ),
    "PREF_EXPLICIT_GENERAL": ReasonCodeDTO(
        code="PREF_EXPLICIT_GENERAL",
        category="GENERAL",
        description="Personalized based on explicit preference settings",
        priority=8,
        explanation_template="Personalized based on your preference of {value} for {key}.",
    ),
    "PREF_IMPLICIT_CLASS": ReasonCodeDTO(
        code="PREF_IMPLICIT_CLASS",
        category="COMFORT",
        description="Personalized based on implicit class comfort predictions",
        priority=5,
        explanation_template="Personalized based on your booking patterns indicating a class preference of {value}.",
    ),
    "PREF_IMPLICIT_SEAT": ReasonCodeDTO(
        code="PREF_IMPLICIT_SEAT",
        category="COMFORT",
        description="Personalized based on implicit seat selection predictions",
        priority=4,
        explanation_template="Personalized based on your observed seat choice pattern of {value}.",
    ),
    "PREF_IMPLICIT_GENERAL": ReasonCodeDTO(
        code="PREF_IMPLICIT_GENERAL",
        category="GENERAL",
        description="Personalized based on behavior patterns",
        priority=3,
        explanation_template="Personalized based on your activity patterns indicating a preference of {value} for {key}.",
    ),
    "PREF_DEFAULT": ReasonCodeDTO(
        code="PREF_DEFAULT",
        category="DEFAULT",
        description="Default settings applied",
        priority=0,
        explanation_template="Default settings applied.",
    ),
}


class ReasonCodeEngine(IReasonCodeEngine):
    def assign(self, decision_context: Dict[str, Any]) -> ReasonCodeDTO:
        key = decision_context.get("preference_key")
        pref_type = decision_context.get("type", "EXPLICIT")

        logger.info("Assigning reason code for key=%s type=%s", key, pref_type)

        if pref_type == "EXPLICIT":
            if key == "preferred_class":
                return PREDEFINED_CODES["PREF_EXPLICIT_CLASS"]
            elif key == "seat_preference":
                return PREDEFINED_CODES["PREF_EXPLICIT_SEAT"]
            else:
                return PREDEFINED_CODES["PREF_EXPLICIT_GENERAL"]
        else:
            if key == "preferred_class":
                return PREDEFINED_CODES["PREF_IMPLICIT_CLASS"]
            elif key == "seat_preference":
                return PREDEFINED_CODES["PREF_IMPLICIT_SEAT"]
            else:
                return PREDEFINED_CODES["PREF_IMPLICIT_GENERAL"]

    def lookup(self, reason_code: str) -> ReasonCodeDTO:
        logger.info("Looking up reason code: %s", reason_code)
        return PREDEFINED_CODES.get(reason_code, PREDEFINED_CODES["PREF_DEFAULT"])
