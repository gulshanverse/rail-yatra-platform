# app/integration/adapters/base.py
import logging
from typing import Dict, Any, Type
from abc import abstractmethod
from pydantic import BaseModel
from app.integration.interfaces import IProviderAdapter, IAuthenticationManager

logger = logging.getLogger("ai-service.integration.adapters.base")


class BaseProviderAdapter(IProviderAdapter):
    def __init__(self, auth_manager: IAuthenticationManager):
        self.auth_manager = auth_manager

    @property
    @abstractmethod
    def provider_id(self) -> str:
        pass

    @abstractmethod
    async def execute_query(
        self, capability: str, params: Dict[str, Any], response_model: Type[BaseModel]
    ) -> BaseModel:
        pass
