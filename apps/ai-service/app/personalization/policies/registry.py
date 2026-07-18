# app/personalization/policies/registry.py
import logging
from typing import Dict, Any, Optional
from app.personalization.config.registry import config_registry

logger = logging.getLogger(__name__)


class PolicyRegistry:
    def __init__(self) -> None:
        pass

    def get_policy(self, policy_key: str) -> Optional[Dict[str, Any]]:
        return config_registry.get_config(policy_key)
