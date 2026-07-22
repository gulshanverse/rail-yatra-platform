"""
Presentation Formatter Layer for Milestone 6.6 AI Response Composer Platform.
Separates presentation formatting from domain logic, providing clean formatters for Markdown,
Cards, Tables, Emergency Banners, Accessibility, Mobile, and Web channels.
"""

from typing import List
from abc import ABC, abstractmethod

from app.composer.domain.aggregates import ResponseComposition


class IResponseFormatter(ABC):
    """Abstract interface for presentation formatters."""

    @abstractmethod
    def format(self, composition: ResponseComposition) -> str:
        """Formats a ResponseComposition aggregate into a presentation output string."""
        pass


class MarkdownFormatter(IResponseFormatter):
    """Formats response as clean, scannable GitHub-flavored Markdown."""

    def format(self, composition: ResponseComposition) -> str:
        if not composition or not composition.summary:
            return ""

        output = [f"**{composition.summary.concise_answer}**\n"]

        for section in composition.sections:
            if section.section_type == "WARNING_BANNER":
                output.append(f"> ⚠️ **{section.content}**\n")
            elif section.section_type == "OPTIONS_TABLE":
                output.append(f"### Options\n{section.content}\n")
            else:
                output.append(f"{section.content}\n")

        if composition.action_chips:
            chips = " | ".join(f"[{c.label}]" for c in composition.action_chips)
            output.append(f"\n*Suggested Actions:* {chips}")

        return "\n".join(output)


class CardFormatter(IResponseFormatter):
    """Formats response as structured visual cards for mobile/web UI rendering."""

    def format(self, composition: ResponseComposition) -> str:
        # Formats as a JSON string representation of card components
        import json
        cards = {
            "summary_card": composition.summary.concise_answer if composition.summary else "",
            "sections": [s.to_dict() for s in composition.sections],
            "actions": [c.label for c in composition.action_chips],
        }
        return json.dumps(cards, indent=2)


class TableFormatter(IResponseFormatter):
    """Formats options matrices into markdown comparison tables."""

    @staticmethod
    def format_options_table(headers: List[str], rows: List[List[str]]) -> str:
        header_row = "| " + " | ".join(headers) + " |"
        sep_row = "| " + " | ".join(["---"] * len(headers)) + " |"
        data_rows = ["| " + " | ".join(row) + " |" for row in rows]
        return "\n".join([header_row, sep_row] + data_rows)


class EmergencyFormatter(IResponseFormatter):
    """Formats high-urgency operational alerts into prominent warning displays."""

    def format(self, composition: ResponseComposition) -> str:
        if not composition or not composition.summary:
            return "⚠️ EMERGENCY OPERATIONAL ALERT"

        return f"""
🚨 ==================================================================== 🚨
EMERGENCY RAILWAY ADVISORY: {composition.summary.concise_answer}
======================================================================
"""


class AccessibilityFormatter(IResponseFormatter):
    """Formats responses for screen readers and senior citizens with high readability."""

    def format(self, composition: ResponseComposition) -> str:
        if not composition or not composition.summary:
            return ""

        # Simplified plain text without complex markdown symbols
        plain_text = composition.summary.concise_answer + "\n\n"
        for s in composition.sections:
            plain_text += s.content + "\n"
        return plain_text.strip()
