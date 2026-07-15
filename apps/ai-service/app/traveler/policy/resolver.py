# app/traveler/policy/resolver.py
from typing import Dict, Any
from app.traveler.interfaces.contracts import IPolicyResolver
from app.traveler.config.registry import get_policy


class PolicyResolver(IPolicyResolver):
    def resolve_policy(self, policy_name: str) -> Dict[str, Any]:
        return get_policy(policy_name)
