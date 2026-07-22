"""
Business Policies for Milestone 6.6 AI Response Composer Platform.
Domain policies enforcing safety, DPDP consent, source credibility, hallucination prevention,
commercial neutrality, and PII regex scrubbing.
"""

from typing import Dict, Any, List, Tuple
import re

from app.composer.domain.value_objects import SourceCredibilityRank


class SafetyOverridesConveniencePolicy:
    """Policy: Operational safety and emergency disruption alerts displace standard recommendations."""

    @staticmethod
    def apply_safety_override(
        is_emergency: bool,
        emergency_banner: str,
        standard_sections: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        if is_emergency:
            return [
                {
                    "section_type": "WARNING_BANNER",
                    "content": f"⚠️ EMERGENCY ADVISORY: {emergency_banner}",
                    "priority": "EMERGENCY",
                }
            ] + standard_sections
        return standard_sections


class ConsentGatedPersonalizationPolicy:
    """Policy: Personal preferences and companion history are injected ONLY when DPDP consent is GRANTED."""

    @staticmethod
    def filter_preferences(
        has_consent: bool,
        raw_preferences: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not has_consent:
            return {}  # Zero-knowledge fallback
        return raw_preferences


class SourceCredibilityPolicy:
    """Policy: Official operational APIs (Rank 1) and Policy (Rank 2) override LLM generative text (Rank 5)."""

    @staticmethod
    def resolve_data_conflict(
        official_data: Dict[str, Any],
        llm_assertion: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], SourceCredibilityRank]:
        # Official operational API overrides LLM assertion
        if official_data:
            return official_data, SourceCredibilityRank.RANK_1_OFFICIAL_API
        return llm_assertion, SourceCredibilityRank.RANK_5_LLM_GENERATIVE


class HallucinationPreventionPolicy:
    """Policy: Refuses to invent railway refund rules or schedules when RAG knowledge data is missing."""

    @staticmethod
    def verify_grounding(knowledge_citations: List[Dict[str, Any]], assertion: str) -> bool:
        if not knowledge_citations:
            return False  # Grounding check failed -> missing RAG citation
        return True


class CommercialNeutralityPolicy:
    """Policy: Ensures train recommendations are ranked purely on user constraints, not commercial bias."""

    @staticmethod
    def rank_options(options: List[Dict[str, Any]], sort_key: str = "duration_minutes") -> List[Dict[str, Any]]:
        return sorted(options, key=lambda x: x.get(sort_key, 9999))


class PIIMaskingPolicy:
    """Policy: Scans and masks PII attributes (names, phone numbers, 10-digit PNR tokens) using regex."""

    # PNR 10-digit pattern, Indian mobile phone pattern
    PNR_REGEX = re.compile(r"\b[2-8]\d{9}\b")
    PHONE_REGEX = re.compile(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b")

    @classmethod
    def mask_pii_string(cls, text: str) -> str:
        if not text:
            return ""
        # Mask 10-digit PNR tokens
        text = cls.PNR_REGEX.sub(lambda m: m.group(0)[:3] + "****" + m.group(0)[7:], text)
        # Mask 10-digit phone numbers
        text = cls.PHONE_REGEX.sub(lambda m: m.group(0)[:3] + "*****" + m.group(0)[8:], text)
        return text

    @classmethod
    def mask_traveler_name(cls, full_name: str) -> str:
        if not full_name or len(full_name.strip()) <= 2:
            return "T*******r"
        parts = full_name.strip().split()
        masked_parts = []
        for p in parts:
            if len(p) <= 2:
                masked_parts.append(p[0] + "*")
            else:
                masked_parts.append(p[0] + "*" * (len(p) - 2) + p[-1])
        return " ".join(masked_parts)
