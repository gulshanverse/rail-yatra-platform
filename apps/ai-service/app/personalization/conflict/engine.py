# app/personalization/conflict/engine.py
import logging
from typing import List, Dict, Any
from app.personalization.interfaces.contracts import IConflictResolutionEngine
from app.personalization.dto.models import TravelerPreferenceDTO

logger = logging.getLogger(__name__)


class ConflictResolutionEngine(IConflictResolutionEngine):
    def resolve(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[TravelerPreferenceDTO]:
        logger.info("Resolving conflicts across %d preferences", len(preferences))

        grouped: Dict[str, List[TravelerPreferenceDTO]] = {}
        for pref in preferences:
            grouped.setdefault(pref.preference_key, []).append(pref)

        resolved = []
        for key, prefs in grouped.items():
            if len(prefs) == 1:
                resolved.append(prefs[0])
                continue

            explicit = [p for p in prefs if p.type == "EXPLICIT"]
            implicit = [p for p in prefs if p.type == "IMPLICIT"]

            if explicit:
                winner = max(
                    explicit, key=lambda x: (x.version, x.updated_at or x.created_at)
                )
                resolved.append(winner)
                logger.info(
                    "Conflict resolved: explicit preference wins for key=%s", key
                )
            elif implicit:
                winner = max(
                    implicit,
                    key=lambda x: (
                        float(x.metadata.get("confidence_score", 0.0) or 0.0),
                        x.version,
                        x.updated_at or x.created_at,
                    ),
                )
                resolved.append(winner)
                logger.info(
                    "Conflict resolved: highest confidence implicit preference wins for key=%s",
                    key,
                )

        return resolved

    def detect_conflicts(
        self, preferences: List[TravelerPreferenceDTO]
    ) -> List[Dict[str, Any]]:
        logger.info("Detecting conflicts across %d preferences", len(preferences))
        grouped: Dict[str, List[TravelerPreferenceDTO]] = {}
        for pref in preferences:
            grouped.setdefault(pref.preference_key, []).append(pref)

        conflicts = []
        for key, prefs in grouped.items():
            if len(prefs) <= 1:
                continue

            explicit = [p for p in prefs if p.type == "EXPLICIT"]
            implicit = [p for p in prefs if p.type == "IMPLICIT"]

            if explicit and implicit:
                conflicts.append(
                    {
                        "preference_key": key,
                        "conflict_type": "EXPLICIT_IMPLICIT_OVERRIDE",
                        "details": f"Explicit preference overrides {len(implicit)} implicit preference(s).",
                    }
                )
            elif len(explicit) > 1:
                conflicts.append(
                    {
                        "preference_key": key,
                        "conflict_type": "MULTIPLE_EXPLICIT_VALUES",
                        "details": f"Found {len(explicit)} explicit values for the same preference key.",
                    }
                )
            elif len(implicit) > 1:
                unique_values = {str(p.value) for p in implicit}
                if len(unique_values) > 1:
                    conflicts.append(
                        {
                            "preference_key": key,
                            "conflict_type": "MULTIPLE_IMPLICIT_VALUES",
                            "details": f"Found conflicting implicit values: {list(unique_values)}.",
                        }
                    )

        logger.info("Detected %d conflict scenarios", len(conflicts))
        return conflicts
