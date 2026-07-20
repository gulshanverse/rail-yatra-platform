import logging
from typing import List, Protocol, runtime_checkable
from app.orchestrator.state import AIState
from app.orchestrator.config import platform_config

logger = logging.getLogger("ai-service.orchestrator.policy")


@runtime_checkable
class IWorkflowPolicy(Protocol):
    """
    Protocol contract representing an executable workflow governance policy.
    """

    name: str

    def evaluate(self, state: AIState) -> bool:
        """Evaluates policy and returns True if compliant, False otherwise."""
        ...


class LengthLimitPolicy(IWorkflowPolicy):
    """
    Enforces maximum token or character bounds on traveler prompt strings.
    """

    name: str = "LengthLimitPolicy"

    def evaluate(self, state: AIState) -> bool:
        limit = platform_config.get("resource_limits", {}).get(
            "max_message_length", 4096
        )
        msg_len = len(state.get("message", ""))
        if msg_len > limit:
            logger.warning(
                f"LengthLimitPolicy mismatch: prompt length {msg_len} exceeds limit {limit}"
            )
            return False
        return True


class ProviderEligibilityPolicy(IWorkflowPolicy):
    """
    Enforces governance compliance on allowed LLM backend providers.
    """

    name: str = "ProviderEligibilityPolicy"

    def evaluate(self, state: AIState) -> bool:
        allowed = platform_config.get("governance", {}).get("allowed_providers", [])
        requested_provider = state.get("context", {}).get(
            "requested_provider", "synthetic"
        )
        if requested_provider not in allowed:
            logger.warning(
                f"ProviderEligibilityPolicy mismatch: provider '{requested_provider}' not in {allowed}"
            )
            return False
        return True


class WorkflowPolicyEngine:
    """
    Governance orchestrator evaluating policy registers prior to running nodes.
    """

    def __init__(self) -> None:
        self._policies: List[IWorkflowPolicy] = [
            LengthLimitPolicy(),
            ProviderEligibilityPolicy(),
        ]

    def register_policy(self, policy: IWorkflowPolicy) -> None:
        """Registers a dynamic policy to the evaluation pipeline."""
        self._policies.append(policy)
        logger.info(f"Registered workflow policy: {policy.name}")

    def evaluate_all(self, state: AIState) -> List[str]:
        """
        Evaluates all policies.
        Returns a list of failed policy name strings. If compliant, returns an empty list.
        """
        failures: List[str] = []
        for policy in self._policies:
            try:
                if not policy.evaluate(state):
                    failures.append(policy.name)
            except Exception as e:
                logger.error(
                    f"Error evaluating policy '{policy.name}': {e}", exc_info=True
                )
                failures.append(f"{policy.name}_Error: {str(e)}")
        return failures


class AIGovernanceLayer:
    """
    Compliance wrapper verifying platform rules and context protections.
    """

    def __init__(self, policy_engine: WorkflowPolicyEngine) -> None:
        self._policy_engine = policy_engine

    def verify_governance(self, state: AIState) -> bool:
        """
        Enforces governance metrics.
        Returns True if compliant, False if blocked by policies.
        """
        failures = self._policy_engine.evaluate_all(state)
        if failures:
            state["errors"].extend(
                [f"Governance check failed for policy: {f}" for f in failures]
            )
            return False
        return True


# Global instances for policy and governance
policy_engine = WorkflowPolicyEngine()
governance_layer = AIGovernanceLayer(policy_engine)
