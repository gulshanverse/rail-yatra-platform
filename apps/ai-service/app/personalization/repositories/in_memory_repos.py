# app/personalization/repositories/in_memory_repos.py
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.personalization.interfaces.contracts import (
    IPreferenceRepository,
    IBehaviorRepository,
    IObservationRepository,
    ILearningRepository,
    IConfidenceRepository,
    IReasonCodeRepository,
    IPolicyRepository,
    IConfigurationRepository,
    IAuditRepository,
    IMetricsRepository,
    ICacheRepository,
    IEventPublisher,
)
from app.personalization.dto.models import (
    TravelerPreferenceDTO,
    TravelerBehaviorDTO,
    LearningObservationDTO,
    PreferenceConfidenceDTO,
    ReasonCodeDTO,
    PreferenceAuditDTO,
    PreferenceMetricsDTO,
)

logger = logging.getLogger(__name__)


class InMemoryPreferenceRepository(IPreferenceRepository):
    def __init__(self) -> None:
        self._preferences: Dict[str, List[TravelerPreferenceDTO]] = {}

    def get_by_traveler_id(self, traveler_id: str) -> List[TravelerPreferenceDTO]:
        return self._preferences.get(traveler_id, [])

    def save(self, preference: TravelerPreferenceDTO) -> None:
        traveler_id = preference.traveler_profile_id
        if traveler_id not in self._preferences:
            self._preferences[traveler_id] = []

        # Update if exists, else append
        existing_list = self._preferences[traveler_id]
        for i, pref in enumerate(existing_list):
            if pref.preference_id == preference.preference_id or (
                pref.preference_key == preference.preference_key
                and pref.category == preference.category
            ):
                existing_list[i] = preference
                logger.debug(
                    "Updated preference_id=%s for traveler=%s",
                    preference.preference_id,
                    traveler_id,
                )
                return

        existing_list.append(preference)
        logger.debug(
            "Saved preference_id=%s for traveler=%s",
            preference.preference_id,
            traveler_id,
        )

    def delete_by_traveler_id(self, traveler_id: str) -> None:
        if traveler_id in self._preferences:
            del self._preferences[traveler_id]
            logger.info("Deleted preferences for traveler=%s", traveler_id)


class InMemoryBehaviorRepository(IBehaviorRepository):
    def __init__(self) -> None:
        self._behaviors: Dict[str, TravelerBehaviorDTO] = {}

    def get_by_traveler_id(self, traveler_id: str) -> Optional[TravelerBehaviorDTO]:
        return self._behaviors.get(traveler_id)

    def save(self, behavior: TravelerBehaviorDTO) -> None:
        self._behaviors[behavior.traveler_profile_id] = behavior
        logger.debug("Saved behavior for traveler=%s", behavior.traveler_profile_id)


class InMemoryObservationRepository(IObservationRepository):
    def __init__(self) -> None:
        self._observations: Dict[str, List[LearningObservationDTO]] = {}

    def get_by_traveler_id_and_window(
        self, traveler_id: str, start_time: datetime, end_time: datetime
    ) -> List[LearningObservationDTO]:
        obs_list = self._observations.get(traveler_id, [])
        return [obs for obs in obs_list if start_time <= obs.timestamp <= end_time]

    def save(self, observation: LearningObservationDTO) -> None:
        traveler_id = observation.traveler_id
        if traveler_id not in self._observations:
            self._observations[traveler_id] = []
        self._observations[traveler_id].append(observation)
        logger.debug("Saved observation for traveler=%s", traveler_id)

    def delete_expired(self) -> int:
        now = datetime.utcnow()
        deleted_count = 0
        for traveler_id, obs_list in list(self._observations.items()):
            active_obs = [obs for obs in obs_list if obs.ttl_expiry > now]
            deleted_count += len(obs_list) - len(active_obs)
            if active_obs:
                self._observations[traveler_id] = active_obs
            else:
                del self._observations[traveler_id]
        return deleted_count


class InMemoryLearningRepository(ILearningRepository):
    def __init__(self) -> None:
        self._sessions: Dict[str, List[Dict[str, Any]]] = {}

    def get_active_sessions(self, traveler_id: str) -> List[Dict[str, Any]]:
        return self._sessions.get(traveler_id, [])

    def save_session(self, session: Dict[str, Any]) -> None:
        traveler_id = session.get("traveler_id")
        if not traveler_id:
            return
        if traveler_id not in self._sessions:
            self._sessions[traveler_id] = []

        session_id = session.get("session_id")
        existing_list = self._sessions[traveler_id]
        for i, s in enumerate(existing_list):
            if s.get("session_id") == session_id:
                existing_list[i] = session
                return
        existing_list.append(session)


class InMemoryConfidenceRepository(IConfidenceRepository):
    def __init__(self) -> None:
        self._confidence_scores: Dict[str, PreferenceConfidenceDTO] = {}

    def get_by_preference_id(
        self, preference_id: str
    ) -> Optional[PreferenceConfidenceDTO]:
        return self._confidence_scores.get(preference_id)

    def save(self, confidence: PreferenceConfidenceDTO) -> None:
        self._confidence_scores[confidence.preference_id] = confidence


class InMemoryReasonCodeRepository(IReasonCodeRepository):
    def __init__(self) -> None:
        self._reason_codes: Dict[str, ReasonCodeDTO] = {
            "PREF_EXPLICIT_CLASS": ReasonCodeDTO(
                code="PREF_EXPLICIT_CLASS",
                category="COMFORT",
                description="Explicit preferred travel class setting.",
                priority=10,
                explanation_template="We applied your explicit choice of travel class: {value}.",
            ),
            "PREF_EXPLICIT_SEAT": ReasonCodeDTO(
                code="PREF_EXPLICIT_SEAT",
                category="COMFORT",
                description="Explicit preferred seat setting.",
                priority=10,
                explanation_template="We reserved your explicit choice of seat preference: {value}.",
            ),
            "PREF_IMPLICIT_MEAL": ReasonCodeDTO(
                code="PREF_IMPLICIT_MEAL",
                category="DIETARY",
                description="Implicit dietary preference learned from food ordering history.",
                priority=5,
                explanation_template="Based on your ordering habits, we pre-selected a {value} meal.",
            ),
            "PREF_DEFAULT_FALLBACK": ReasonCodeDTO(
                code="PREF_DEFAULT_FALLBACK",
                category="SYSTEM",
                description="Default system fallback setting.",
                priority=0,
                explanation_template="Default option selected.",
            ),
        }

    def get_by_code(self, code: str) -> Optional[ReasonCodeDTO]:
        return self._reason_codes.get(code)


class InMemoryPolicyRepository(IPolicyRepository):
    def __init__(self) -> None:
        # Initialized with empty config; will defer to registry defaults
        self._policies: Dict[str, Dict[str, Any]] = {}

    def get_policy(self, policy_key: str) -> Optional[Dict[str, Any]]:
        return self._policies.get(policy_key)

    def save_policy(self, policy_key: str, policy_data: Dict[str, Any]) -> None:
        self._policies[policy_key] = policy_data


class InMemoryConfigurationRepository(IConfigurationRepository):
    def __init__(self) -> None:
        self._configs: Dict[str, Any] = {}

    def get_config(self, key: str) -> Optional[Any]:
        return self._configs.get(key)

    def set_config(self, key: str, value: Any) -> None:
        self._configs[key] = value


class InMemoryAuditRepository(IAuditRepository):
    def __init__(self) -> None:
        self._audits: Dict[str, PreferenceAuditDTO] = {}

    def save(self, audit: PreferenceAuditDTO) -> None:
        self._audits[audit.audit_id] = audit

    def get_by_id(self, audit_id: str) -> Optional[PreferenceAuditDTO]:
        return self._audits.get(audit_id)


class InMemoryMetricsRepository(IMetricsRepository):
    def __init__(self) -> None:
        self._metrics: List[PreferenceMetricsDTO] = []

    def save(self, metric: PreferenceMetricsDTO) -> None:
        self._metrics.append(metric)


class InMemoryCacheRepository(ICacheRepository):
    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}

    def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._cache[key] = value

    def delete(self, key: str) -> None:
        if key in self._cache:
            del self._cache[key]


class LoggingEventPublisher(IEventPublisher):
    async def publish_event(self, name: str, payload: Dict[str, Any]) -> None:
        logger.info("Published domain event name=%s payload=%s", name, payload)
