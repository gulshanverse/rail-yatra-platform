"""
Serialization utilities for the RailYatra AI Memory Layer.
Uses JSON only to ensure compatibility, readability, and security.
"""

import json
from typing import Any, Type, TypeVar
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class MemorySerializer:
    """
    Standard serializer using JSON to load/dump memory states.
    Ensures safe payload structures and handles schema evolution placeholders.
    """

    @staticmethod
    def serialize(obj: Any) -> str:
        """
        Serializes pydantic models or dicts to JSON format.
        """
        if isinstance(obj, BaseModel):
            return obj.model_dump_json()
        return json.dumps(obj)

    @staticmethod
    def deserialize(data: str, target_type: Type[T]) -> T:
        """
        Deserializes a JSON string into a target Pydantic model.
        Supports schema version mapping.
        """
        parsed = json.loads(data)
        if issubclass(target_type, BaseModel):
            # Check for version compatibility if required in future evolutions
            return target_type.model_validate(parsed)
        return parsed
