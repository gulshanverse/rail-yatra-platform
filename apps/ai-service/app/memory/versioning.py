"""
OCC version comparison, increment boundaries, and verification logic.
"""

from typing import Optional
from app.config.config import settings
from app.memory.exceptions import MemoryVersionError


class MemoryVersionConflict(MemoryVersionError):
    """Raised when expected session state version does not match current version."""

    pass


class VersionManager:
    """Manages version check and comparisons."""

    @staticmethod
    def compare_versions(current_version: int, expected_version: int) -> int:
        """
        Compares version values.
        Returns:
            0 if current == expected
            -1 if current < expected
            1 if current > expected
        """
        if current_version == expected_version:
            return 0
        return -1 if current_version < expected_version else 1

    @staticmethod
    def increment(current_version: int) -> int:
        """Increments version number by 1."""
        return current_version + 1

    @staticmethod
    def validate_occ(current_version: int, expected_version: Optional[int]) -> None:
        """
        Compares expected and actual versions.
        Raises MemoryVersionConflict if mismatch is detected.
        """
        if expected_version is None or not settings.OCC_ENABLED:
            return

        comp = VersionManager.compare_versions(current_version, expected_version)
        if comp != 0:
            raise MemoryVersionConflict(
                f"Optimistic Concurrency conflict: Expected version {expected_version}, "
                f"but database has version {current_version}."
            )
