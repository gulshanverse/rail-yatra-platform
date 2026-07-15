"""
Document Processing pipelines: Text cleaning, PII Redaction, Language detection, and Trust Scoring.
"""

import re
import logging
from typing import Dict, Any, Tuple, List

from app.knowledge.interfaces import IDocumentProcessor
from app.knowledge.exceptions import ProcessingException

logger = logging.getLogger("ai-service.knowledge.processing")


class TextCleanerProcessor(IDocumentProcessor):
    """Normalizes whitespace and removes control characters from text payloads."""

    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        try:
            text = content.decode("utf-8")
            # Remove control characters except tab and newline
            cleaned_text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
            # Normalize whitespace sequences (except newlines)
            cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
            return cleaned_text.encode("utf-8"), metadata
        except Exception as e:
            raise ProcessingException(f"Text cleaning stage failed: {e}")


class PIIRedactorProcessor(IDocumentProcessor):
    """Filters sensitive data such as email addresses, phone numbers, and 10-digit PNR codes."""

    # 10-digit sequence for PNR numbers
    PNR_PATTERN = re.compile(r"\b\d{10}\b")
    EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
    PHONE_PATTERN = re.compile(r"\b(?:\+?\d{1,3}[- ]?)?\d{10}\b")

    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        try:
            text = content.decode("utf-8")
            # Redact email patterns
            text = self.EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
            # Redact PNR codes (10 digit integers)
            text = self.PNR_PATTERN.sub("[REDACTED_PNR]", text)
            # Redact general phone numbers
            text = self.PHONE_PATTERN.sub("[REDACTED_PHONE]", text)

            return text.encode("utf-8"), metadata
        except Exception as e:
            raise ProcessingException(f"PII Redaction stage failed: {e}")


class LanguageDetectorProcessor(IDocumentProcessor):
    """Identifies document language based on vocabulary distributions."""

    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        try:
            text = content.decode("utf-8").lower()

            # Simple keyword checks to identify Hindi (Devanagari character sets) vs English
            hindi_chars = len(re.findall(r"[\u0900-\u097f]", text))
            english_words = len(
                re.findall(
                    r"\b(?:the|and|railway|train|passenger|is|at|on|for|of)\b", text
                )
            )

            detected_lang = "en"
            if hindi_chars > english_words * 2:
                detected_lang = "hi"

            updated_metadata = dict(metadata)
            updated_metadata["language"] = detected_lang
            return content, updated_metadata
        except Exception as e:
            raise ProcessingException(f"Language detection stage failed: {e}")


class ContentValidatorProcessor(IDocumentProcessor):
    """Ensures document text passes basic size, trust, and validation rules."""

    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        if not content:
            raise ProcessingException("Corrupt content payload: text content is empty")

        try:
            text = content.decode("utf-8")
            if len(text.strip()) < 10:
                raise ProcessingException(
                    "Quality validation failed: document content is too short (min 10 chars)"
                )
            return content, metadata
        except UnicodeDecodeError:
            raise ProcessingException(
                "Corrupt content payload: text does not conform to UTF-8 encoding"
            )


class QualityScorerProcessor(IDocumentProcessor):
    """Calculates initial Trust and Quality Metrics based on organizational authority."""

    def process(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        updated_metadata = dict(metadata)

        # Determine authority level based on organization metadata properties
        authority = updated_metadata.get("authority_level", "unknown").lower()

        if authority == "railway_board":
            auth_score = 1.0
        elif authority in ("zone", "zonal"):
            auth_score = 0.8
        elif authority in ("division", "divisional"):
            auth_score = 0.6
        else:
            auth_score = 0.4

        # Calculate completeness score based on key metadata variables existence
        key_metadata_keys = ["document_id", "category", "tags"]
        exists_count = sum(1 for k in key_metadata_keys if k in updated_metadata)
        completeness_score = exists_count / len(key_metadata_keys)

        # Average freshness is 1.0 at initial ingestion
        freshness_score = 1.0

        # Composite score calculation
        composite_score = (
            (0.25 * freshness_score)
            + (0.35 * auth_score)
            + (0.20 * completeness_score)
            + (0.20 * 1.0)  # General initial trust
        )

        updated_metadata["trust_score"] = float(round(composite_score, 2))
        updated_metadata["authority_score"] = auth_score
        updated_metadata["freshness_score"] = freshness_score

        return content, updated_metadata


class ProcessingPipeline:
    """Orchestrator executing configured document processing pipelines."""

    def __init__(self, processors: List[IDocumentProcessor] = None) -> None:
        self.processors = processors or [
            TextCleanerProcessor(),
            PIIRedactorProcessor(),
            LanguageDetectorProcessor(),
            ContentValidatorProcessor(),
            QualityScorerProcessor(),
        ]

    def execute(
        self, content: bytes, metadata: Dict[str, Any]
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Processes content sequentially through active stages."""
        current_content = content
        current_metadata = dict(metadata)

        for idx, processor in enumerate(self.processors):
            try:
                current_content, current_metadata = processor.process(
                    current_content, current_metadata
                )
            except ProcessingException as pe:
                logger.error(
                    f"Pipeline error at stage {idx} ({type(processor).__name__}): {pe}"
                )
                raise pe
            except Exception as e:
                logger.error(
                    f"Unexpected pipeline crash at stage {idx} ({type(processor).__name__}): {e}"
                )
                raise ProcessingException(f"Pipeline crashed during execution: {e}")

        return current_content, current_metadata
