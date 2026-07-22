"""
Centralized Prompt Management Framework for Milestone 6.6 AI Response Composer Platform.
Provides prompt versioning, template management, system prompts, task prompts, few-shot examples,
and prompt rollback capabilities.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import time


@dataclass
class PromptVersion:
    """Represents a specific versioned prompt configuration."""

    version_id: str
    system_prompt: str
    task_template: str
    few_shot_examples: List[Dict[str, str]] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    is_active: bool = True


class PromptRegistry:
    """Centralized prompt repository decoupling prompts from code logic."""

    def __init__(self):
        self._registry: Dict[str, List[PromptVersion]] = {}
        self._initialize_default_prompts()

    def _initialize_default_prompts(self) -> None:
        """Initializes default production system prompts."""

        # 1. System Prompt for Response Composition
        composer_v1 = PromptVersion(
            version_id="v1.0.0",
            system_prompt=(
                "You are the RailYatra AI Response Composer. "
                "Synthesize multi-source railway data into clear, scannable, justified, and persona-adapted responses. "
                "Always lead with the concise answer. Disclose prediction uncertainty transparently. "
                "Respect DPDP privacy gates and offer 2-3 logical action guidance chips."
            ),
            task_template="Passenger Query: {prompt}\nContext: {context}\nFormat: Markdown",
            few_shot_examples=[
                {
                    "input": "Waitlist odds for Train 12951?",
                    "output": "**85% Confirmation Odds (High Confidence).** Historical chart trends show 2 extra coaches usually allocated.",
                }
            ],
        )

        # 2. System Prompt for Explainability Reasoning
        explainer_v1 = PromptVersion(
            version_id="v1.0.0",
            system_prompt=(
                "You are the RailYatra Explainability Engine. "
                "Generate transparent evidence chains justifying predictions and travel choices. "
                "Cite official IRCTC refund rules when explaining policy assertions."
            ),
            task_template="Prediction: {prediction}\nPolicy: {policy}\nExplain Depth Level: {depth}",
            few_shot_examples=[],
        )

        self._registry["COMPOSER_MAIN"] = [composer_v1]
        self._registry["EXPLAINER_MAIN"] = [explainer_v1]

    def get_prompt(self, key: str, version_id: Optional[str] = None) -> PromptVersion:
        """Retrieves active prompt or specific version."""
        versions = self._registry.get(key.upper(), [])
        if not versions:
            raise KeyError(f"Prompt key '{key}' not found in registry.")

        if version_id:
            for v in versions:
                if v.version_id == version_id:
                    return v
            raise KeyError(f"Prompt version '{version_id}' not found for key '{key}'.")

        # Return latest active version
        for v in reversed(versions):
            if v.is_active:
                return v
        return versions[-1]

    def register_prompt(self, key: str, version: PromptVersion) -> None:
        """Registers a new prompt version."""
        key_upper = key.upper()
        if key_upper not in self._registry:
            self._registry[key_upper] = []
        self._registry[key_upper].append(version)

    def rollback_prompt(self, key: str, target_version_id: str) -> None:
        """Rolls back to a target prompt version by deactivating newer versions."""
        versions = self._registry.get(key.upper(), [])
        for v in versions:
            if v.version_id == target_version_id:
                v.is_active = True
            else:
                v.is_active = False


# Singleton prompt registry
prompt_registry = PromptRegistry()
