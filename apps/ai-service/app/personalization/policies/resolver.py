# app/personalization/policies/resolver.py
import logging
from typing import Dict, Any, Optional
from app.personalization.interfaces.contracts import IPolicyResolver
from app.personalization.policies.registry import PolicyRegistry

logger = logging.getLogger(__name__)


class PolicyResolver(IPolicyResolver):
    def __init__(self, registry: Optional[PolicyRegistry] = None) -> None:
        self._registry = registry or PolicyRegistry()

    def resolve(self, policy_key: str, context: Optional[Dict[str, Any]] = None) -> Any:
        policy = self._registry.get_policy(policy_key)
        if policy is None:
            logger.warning("Policy key %s not found, returning empty dict", policy_key)
            return {}
        return policy

    def validate(self, policy_key: str, value: Any) -> bool:
        policy = self.resolve(policy_key)
        if not policy:
            return False
        return True
