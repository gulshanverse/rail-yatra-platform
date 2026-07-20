import re
import logging

logger = logging.getLogger("ai-service.orchestrator.normalizer")


class InputNormalizer:
    """
    Handles text sanitization, whitespace normalization, and PII redaction
    prior to classification and slot extraction.
    """

    def __init__(self):
        # Compiled patterns for PII redaction
        # Support optional parentheses around country code, e.g. (+91) or +91 or 91
        self.phone_pattern = re.compile(r"\b(?:\(?\+?91\)?[\-\s]?)?[6-9]\d{9}\b")
        self.email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b")
        self.pnr_pattern = re.compile(r"\b\d{10}\b")
        self.cc_pattern = re.compile(r"\b(?:\d[ -]*?){13,16}\b")

    def normalize(self, text: str) -> str:
        """Sanitizes text and normalizes whitespace/casing."""
        if not text:
            return ""
        # Strip non-printable characters
        cleaned = "".join(ch for ch in text if ch.isprintable())
        # Normalize spaces
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def redact_pii(self, text: str) -> str:
        """Redacts sensitive traveler information."""
        if not text:
            return ""
        
        redacted = text
        # 1. Redact credit cards
        redacted = self.cc_pattern.sub("[REDACTED_CC]", redacted)
        # 2. Redact phone numbers (run before PNR to avoid treating phone numbers as PNRs)
        redacted = self.phone_pattern.sub("[REDACTED_PHONE]", redacted)
        # 3. Redact PNR (10 digits)
        redacted = self.pnr_pattern.sub("[REDACTED_PNR]", redacted)
        # 4. Redact emails
        redacted = self.email_pattern.sub("[REDACTED_EMAIL]", redacted)
        
        if redacted != text:
            logger.info("PII detected and redacted from user input.")
            
        return redacted


input_normalizer = InputNormalizer()
