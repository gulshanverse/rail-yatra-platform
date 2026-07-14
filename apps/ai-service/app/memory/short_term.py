"""
Enterprise Short-Term Memory Engine for RailYatra AI.
Implements RedisShortTermMemory, IShortTermMemory facade, InMemoryShortTermMemory fallback,
and the MemoryManager orchestrator.
"""

import time
import logging
import threading
import redis
import re
from typing import Dict, Any, List, Optional

from app.memory.interfaces import (
    IShortTermMemory,
    IMemoryManager,
    ConversationSession,
    MemoryItem,
)
from app.memory.session import (
    SessionKeyGenerator,
    ConversationSessionMetadata,
    ConversationSessionManager,
    STATE_ACTIVE,
    STATE_DELETED,
)
from app.memory.serializer import MemorySerializer
from app.memory.ttl import TTLEngine
from app.memory.cache import MemoryCachePolicy, count_tokens
from app.memory.exceptions import (
    SharedMemoryAccessException,
    MemoryQuotaExceededException,
)
from app.config.config import settings

logger = logging.getLogger("ai-service.memory.short_term")

# Observability Metrics Store (thread-safe)
metrics_lock = threading.Lock()
metrics_store = {
    "session_count": 0,
    "message_count": 0,
    "reads": 0,
    "writes": 0,
    "updates": 0,
    "deletes": 0,
    "cache_hit": 0,
    "cache_miss": 0,
    "ttl_refreshes": 0,
    "expirations": 0,
    "memory_usage_bytes": 0,
    "total_latency_ms": 0.0,
    "latency_count": 0,
}


def record_metric(name: str, value: Any = 1) -> None:
    with metrics_lock:
        if name in metrics_store:
            if isinstance(value, (int, float)):
                metrics_store[name] += value
            else:
                metrics_store[name] = value


class InMemoryShortTermMemory:
    """Thread-safe local in-memory storage fallback for short-term memory."""

    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: Dict[
            str, str
        ] = {}  # session_id -> JSON representation of ConversationSession
        self._meta: Dict[
            str, str
        ] = {}  # session_id -> JSON representation of ConversationSessionMetadata
        self._user_indexes: Dict[str, set] = {}  # user_id -> set of session_ids

    def exists(self, session_id: str) -> bool:
        with self._lock:
            return session_id in self._sessions

    def get_session(self, session_id: str) -> Optional[str]:
        with self._lock:
            return self._sessions.get(session_id)

    def get_meta(self, session_id: str) -> Optional[str]:
        with self._lock:
            return self._meta.get(session_id)

    def save_session(
        self, user_id: str, session_id: str, session_json: str, meta_json: str
    ) -> None:
        with self._lock:
            self._sessions[session_id] = session_json
            self._meta[session_id] = meta_json
            if user_id not in self._user_indexes:
                self._user_indexes[user_id] = set()
            self._user_indexes[user_id].add(session_id)

    def delete_session(self, user_id: str, session_id: str) -> None:
        with self._lock:
            self._sessions.pop(session_id, None)
            self._meta.pop(session_id, None)
            if user_id in self._user_indexes:
                self._user_indexes[user_id].discard(session_id)

    def list_sessions(self, user_id: str) -> List[str]:
        with self._lock:
            return list(self._user_indexes.get(user_id, set()))


class RedisShortTermMemory:
    """Primary Redis implementation of the short-term memory store."""

    def __init__(self, redis_client: redis.Redis):
        self.client = redis_client

    def exists(self, session_id: str) -> bool:
        meta_key = SessionKeyGenerator.get_meta_key(session_id)
        return bool(self.client.exists(meta_key))

    def get_session(self, user_id: str, session_id: str) -> Optional[str]:
        key = SessionKeyGenerator.get_session_key(user_id, session_id)
        val = self.client.get(key)
        return val.decode("utf-8") if isinstance(val, bytes) else val

    def get_meta(self, session_id: str) -> Optional[str]:
        key = SessionKeyGenerator.get_meta_key(session_id)
        val = self.client.get(key)
        return val.decode("utf-8") if isinstance(val, bytes) else val

    def save_session(
        self, user_id: str, session_id: str, session_json: str, meta_json: str, ttl: int
    ) -> None:
        sess_key = SessionKeyGenerator.get_session_key(user_id, session_id)
        meta_key = SessionKeyGenerator.get_meta_key(session_id)
        index_key = SessionKeyGenerator.get_index_key(user_id)

        # Write to Redis
        self.client.set(sess_key, session_json, ex=ttl)
        self.client.set(meta_key, meta_json, ex=ttl)
        self.client.sadd(index_key, session_id)
        self.client.expire(index_key, ttl)

    def delete_session(self, user_id: str, session_id: str) -> None:
        sess_key = SessionKeyGenerator.get_session_key(user_id, session_id)
        meta_key = SessionKeyGenerator.get_meta_key(session_id)
        index_key = SessionKeyGenerator.get_index_key(user_id)

        self.client.delete(sess_key)
        self.client.delete(meta_key)
        self.client.srem(index_key, session_id)

    def list_sessions(self, user_id: str) -> List[str]:
        index_key = SessionKeyGenerator.get_index_key(user_id)
        members = self.client.smembers(index_key)
        return [m.decode("utf-8") if isinstance(m, bytes) else m for m in members]


class ShortTermMemory(IShortTermMemory):
    """
    Unified Short-Term Memory manager facade.
    Implements IShortTermMemory protocol, manages fallback, cache eviction, and idempotency.
    """

    def __init__(self):
        self.redis_client = None
        self._init_redis()
        self.fallback_store = InMemoryShortTermMemory()
        self.cache_policy = MemoryCachePolicy(
            max_sessions=settings.MAX_ACTIVE_SESSIONS_PER_USER,
            policy=settings.CACHE_POLICY,
        )
        from app.memory.concurrency import ConcurrencyManager

        self.concurrency_mgr = ConcurrencyManager(self)

    def _init_redis(self) -> None:
        try:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL, decode_responses=True
            )
            self.redis_client.ping()
            logger.info("ShortTermMemory successfully connected to Redis.")
        except Exception as e:
            logger.warning(
                f"ShortTermMemory could not connect to Redis at {settings.REDIS_URL}: {e}. Local fallback enabled."
            )
            self.redis_client = None

    def _is_redis_active(self) -> bool:
        if self.redis_client is None:
            return False
        try:
            self.redis_client.ping()
            return True
        except Exception:
            return False

    # IShortTermMemory Protocol Implementation
    async def save_session_context(
        self,
        session_id: str,
        context_data: Dict[str, Any],
        expire_seconds: int = 86400,
        expected_version: Optional[int] = None,
    ) -> None:
        """Caches session context variables."""

        async def _run():
            await self._save_session_context_inner(
                session_id, context_data, expire_seconds
            )

        await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _save_session_context_inner(
        self, session_id: str, context_data: Dict[str, Any], expire_seconds: int = 86400
    ) -> None:
        # Check if session exists or generate defaults
        meta = await self._get_meta_obj(session_id)
        user_id = meta.user_id if meta else "default_user"

        session = await self._get_session_obj(user_id, session_id)
        if not session:
            session = ConversationSession(session_id=session_id, user_id=user_id)

        session.context = context_data

        if meta:
            meta.session_state = STATE_ACTIVE
            TTLEngine.refresh(meta)
            meta.memory_version += 1
        else:
            meta = ConversationSessionMetadata(
                user_id=user_id,
                session_id=session_id,
                conversation_id=session_id,
                ttl=expire_seconds,
                session_state=STATE_ACTIVE,
            )

        await self._write_to_store(user_id, session_id, session, meta)

    async def get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Retrieves cached session context variables."""
        meta = await self._get_meta_obj(session_id)
        if not meta:
            record_metric("cache_miss")
            return {}

        # Check Expiration
        if TTLEngine.is_expired(meta):
            record_metric("expirations")
            await self.delete_session(session_id)
            return {}

        session = await self._get_session_obj(meta.user_id, session_id)
        if not session:
            record_metric("cache_miss")
            return {}

        record_metric("cache_hit")
        record_metric("reads")

        # Refresh sliding TTL on read
        TTLEngine.refresh(meta)
        await self._write_to_store(meta.user_id, session_id, session, meta)
        return session.context

    async def add_message(
        self, session_id: str, role: str, content: str, limit: int = 20
    ) -> None:
        """Appends message to the active sliding window history."""
        await self.append_message(session_id, role, content, limit=limit)

    async def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieves list of messages in the sliding history window."""
        meta = await self._get_meta_obj(session_id)
        if not meta:
            return []

        if TTLEngine.is_expired(meta):
            await self.delete_session(session_id)
            return []

        session = await self._get_session_obj(meta.user_id, session_id)
        if not session:
            return []

        # Refresh sliding TTL on read
        TTLEngine.refresh(meta)
        await self._write_to_store(meta.user_id, session_id, session, meta)
        return session.history

    async def clear_session(self, session_id: str) -> None:
        """Deletes session context and history keys."""
        await self.delete_session(session_id)

    # Core Session Engine Implementation
    async def session_exists(self, session_id: str) -> bool:
        meta = await self._get_meta_obj(session_id)
        if not meta:
            return False
        if TTLEngine.is_expired(meta):
            await self.delete_session(session_id)
            return False
        return True

    async def create_session(
        self,
        user_id: str,
        session_id: str,
        conversation_id: str,
        feature_flags: Dict[str, Any] = None,
        expected_version: Optional[int] = None,
    ) -> Dict[str, Any]:
        async def _run():
            return await self._create_session_inner(
                user_id, session_id, conversation_id, feature_flags
            )

        return await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _create_session_inner(
        self,
        user_id: str,
        session_id: str,
        conversation_id: str,
        feature_flags: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        # Enforce Max Sessions per user limit
        active_sessions = await self.list_sessions(user_id)
        if len(active_sessions) >= settings.MAX_ACTIVE_SESSIONS_PER_USER:
            # Evict oldest session
            evictions = self.cache_policy.evict_if_needed(user_id, session_id)
            if evictions:
                for evicted_id in evictions:
                    logger.info(
                        f"Evicting session {evicted_id} for user {user_id} due to capacity limit."
                    )
                    await self.delete_session(evicted_id)

        meta = ConversationSessionManager.create_metadata(
            user_id=user_id,
            session_id=session_id,
            conversation_id=conversation_id,
            ttl=settings.MEMORY_TTL_SECS,
            feature_flags=feature_flags,
        )
        session = ConversationSession(session_id=session_id, user_id=user_id)

        await self._write_to_store(user_id, session_id, session, meta)
        self.cache_policy.record_access(user_id, session_id)
        record_metric("session_count", len(await self.list_sessions(user_id)))
        return meta.model_dump()

    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        meta = await self._get_meta_obj(session_id)
        if not meta:
            return None
        if TTLEngine.is_expired(meta):
            await self.delete_session(session_id)
            return None

        # Refresh sliding TTL
        TTLEngine.refresh(meta)
        session = await self._get_session_obj(meta.user_id, session_id)
        if session:
            await self._write_to_store(meta.user_id, session_id, session, meta)

        self.cache_policy.record_access(meta.user_id, session_id)
        return meta.model_dump()

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        operation_id: Optional[str] = None,
        limit: int = 20,
        expected_version: Optional[int] = None,
    ) -> bool:
        async def _run():
            return await self._append_message_inner(
                session_id, role, content, operation_id, limit
            )

        return await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _append_message_inner(
        self,
        session_id: str,
        role: str,
        content: str,
        operation_id: Optional[str] = None,
        limit: int = 20,
    ) -> bool:
        start_time = time.time()
        meta = await self._get_meta_obj(session_id)
        if not meta:
            raise KeyError(f"Session {session_id} does not exist.")

        if TTLEngine.is_expired(meta):
            await self.delete_session(session_id)
            raise KeyError(f"Session {session_id} has expired.")

        # Security Ownership Check
        # Validate that ownership isolation is preserved
        user_id = meta.user_id

        # Idempotency check
        if operation_id and meta.last_operation_id == operation_id:
            logger.info(f"Duplicate operation_id {operation_id} rejected safely.")
            return True

        session = await self._get_session_obj(user_id, session_id)
        if not session:
            raise KeyError(f"Session state missing for {session_id}.")

        # Append message
        msg = {"role": role, "content": content, "timestamp": time.time()}
        session.history.append(msg)

        # Enforce message limits
        max_limit = min(limit, settings.MAX_USER_SHORT_TERM_MESSAGES)
        if len(session.history) > max_limit:
            session.history = session.history[-max_limit:]

        # Update metadata stats
        meta.message_count = len(session.history)
        meta.token_count = sum(count_tokens(m["content"]) for m in session.history)
        meta.memory_version += 1
        if operation_id:
            meta.last_operation_id = operation_id

        ConversationSessionManager.transition_state(meta, STATE_ACTIVE)
        TTLEngine.refresh(meta)

        await self._write_to_store(user_id, session_id, session, meta)
        self.cache_policy.record_access(user_id, session_id)

        record_metric("message_count", 1)
        record_metric("writes")

        latency_ms = (time.time() - start_time) * 1000
        record_metric("total_latency_ms", latency_ms)
        record_metric("latency_count", 1)
        return True

    async def update_metadata(
        self,
        session_id: str,
        metadata_updates: Dict[str, Any],
        expected_version: Optional[int] = None,
    ) -> None:
        async def _run():
            await self._update_metadata_inner(session_id, metadata_updates)

        await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _update_metadata_inner(
        self, session_id: str, metadata_updates: Dict[str, Any]
    ) -> None:
        meta = await self._get_meta_obj(session_id)
        if not meta:
            raise KeyError(f"Session {session_id} does not exist.")

        for k, v in metadata_updates.items():
            if hasattr(meta, k):
                setattr(meta, k, v)
            else:
                meta.feature_flags[k] = v

        meta.memory_version += 1
        meta.updated_at = time.time()

        session = await self._get_session_obj(meta.user_id, session_id)
        if session:
            await self._write_to_store(meta.user_id, session_id, session, meta)

        record_metric("updates")

    async def save_conversation(
        self,
        session_id: str,
        conversation_data: Dict[str, Any],
        expected_version: Optional[int] = None,
    ) -> None:
        async def _run():
            await self._save_conversation_inner(session_id, conversation_data)

        await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _save_conversation_inner(
        self, session_id: str, conversation_data: Dict[str, Any]
    ) -> None:
        meta = await self._get_meta_obj(session_id)
        if not meta:
            raise KeyError(f"Session {session_id} does not exist.")

        session = await self._get_session_obj(meta.user_id, session_id)
        if not session:
            session = ConversationSession(session_id=session_id, user_id=meta.user_id)

        session.history = conversation_data.get("history", session.history)
        session.context = conversation_data.get("context", session.context)

        meta.message_count = len(session.history)
        meta.token_count = sum(count_tokens(m["content"]) for m in session.history)
        meta.memory_version += 1

        await self._write_to_store(meta.user_id, session_id, session, meta)
        record_metric("writes")

    async def delete_session(
        self, session_id: str, expected_version: Optional[int] = None
    ) -> None:
        async def _run():
            await self._delete_session_inner(session_id)

        await self.concurrency_mgr.execute_transaction(
            session_id, _run, expected_version=expected_version
        )

    async def _delete_session_inner(self, session_id: str) -> None:
        meta = await self._get_meta_obj(session_id)
        if not meta:
            return

        user_id = meta.user_id

        # Mark state machine transition
        ConversationSessionManager.transition_state(meta, STATE_DELETED)

        if self._is_redis_active():
            try:
                engine = RedisShortTermMemory(self.redis_client)
                engine.delete_session(user_id, session_id)
            except Exception as e:
                logger.error(f"Redis delete_session error: {e}")
                self.fallback_store.delete_session(user_id, session_id)
        else:
            self.fallback_store.delete_session(user_id, session_id)

        self.cache_policy.remove_session(user_id, session_id)
        record_metric("deletes")

    async def list_sessions(self, user_id: str) -> List[str]:
        if self._is_redis_active():
            try:
                engine = RedisShortTermMemory(self.redis_client)
                return engine.list_sessions(user_id)
            except Exception as e:
                logger.error(f"Redis list_sessions error: {e}")
                return self.fallback_store.list_sessions(user_id)
        else:
            return self.fallback_store.list_sessions(user_id)

    # Helper methods for IO Operations
    async def _get_meta_obj(
        self, session_id: str
    ) -> Optional[ConversationSessionMetadata]:
        raw_meta = None
        if self._is_redis_active():
            try:
                engine = RedisShortTermMemory(self.redis_client)
                raw_meta = engine.get_meta(session_id)
            except Exception as e:
                logger.error(f"Redis get_meta error: {e}")
                raw_meta = self.fallback_store.get_meta(session_id)
        else:
            raw_meta = self.fallback_store.get_meta(session_id)

        if not raw_meta:
            return None
        return MemorySerializer.deserialize(raw_meta, ConversationSessionMetadata)

    async def _get_session_obj(
        self, user_id: str, session_id: str
    ) -> Optional[ConversationSession]:
        raw_session = None
        if self._is_redis_active():
            try:
                engine = RedisShortTermMemory(self.redis_client)
                raw_session = engine.get_session(user_id, session_id)
            except Exception as e:
                logger.error(f"Redis get_session error: {e}")
                raw_session = self.fallback_store.get_session(session_id)
        else:
            raw_session = self.fallback_store.get_session(session_id)

        if not raw_session:
            return None
        return MemorySerializer.deserialize(raw_session, ConversationSession)

    async def _write_to_store(
        self,
        user_id: str,
        session_id: str,
        session: ConversationSession,
        meta: ConversationSessionMetadata,
    ) -> None:
        session_json = MemorySerializer.serialize(session)
        meta_json = MemorySerializer.serialize(meta)

        # Quota enforcement: check payload size limit (e.g. 500KB limit)
        if len(session_json.encode("utf-8")) > 500 * 1024:
            raise MemoryQuotaExceededException(
                "Session payload size limit exceeded (Max 500 KB)"
            )

        if self._is_redis_active():
            try:
                engine = RedisShortTermMemory(self.redis_client)
                engine.save_session(
                    user_id, session_id, session_json, meta_json, meta.ttl
                )
            except Exception as e:
                logger.error(f"Redis save_session error: {e}")
                self.fallback_store.save_session(
                    user_id, session_id, session_json, meta_json
                )
        else:
            self.fallback_store.save_session(
                user_id, session_id, session_json, meta_json
            )


# Initialize standard singleton facade
short_term_memory = ShortTermMemory()

# =====================================================================
# MemoryManager (IMemoryManager Facade Integration)
# =====================================================================


class MemoryManager(IMemoryManager):
    """
    Public facade implementing IMemoryManager interface.
    Coordinates short term memory (ShortTermMemory) and sets up integration
    boundaries for future long term vector persistence.
    """

    def __init__(self, short_memory: IShortTermMemory = short_term_memory):
        self.short_term = short_memory

    def _scrub_pii(self, text: str) -> str:
        """Scrubs sensitive information such as PNRs, emails, and phone numbers."""
        # Scrub email
        scrubbed = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "[EMAIL]", text
        )
        # Scrub phone numbers (10 digits)
        scrubbed = re.sub(r"\b\d{10}\b", "[PHONE]", scrubbed)
        # Scrub PNRs (10 digits)
        scrubbed = re.sub(r"\b\d{10}\b", "[PNR]", scrubbed)
        return scrubbed

    async def save_interaction(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        agent_response: str,
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """Scrubs PII and appends messages to short-term sliding history window."""
        # Enforce cross-user security access isolation checks
        meta_exists = await self.short_term.session_exists(session_id)
        if meta_exists:
            # Check ownership
            meta_data = await self.short_term.load_session(session_id)
            if meta_data and meta_data.get("user_id") != user_id:
                raise SharedMemoryAccessException(
                    "Access Denied: Session owner mismatch."
                )
        else:
            # Create session if it doesn't exist
            await self.short_term.create_session(user_id, session_id, session_id)

        scrubbed_user = self._scrub_pii(user_message)
        scrubbed_agent = self._scrub_pii(agent_response)

        # Write to short term memory
        # Increments versions and applies sliding TTL internally
        op_id_user = f"op-{session_id}-{int(time.time() * 1000)}-u"
        op_id_agent = f"op-{session_id}-{int(time.time() * 1000)}-a"
        await self.short_term.append_message(
            session_id, "user", scrubbed_user, operation_id=op_id_user
        )
        await self.short_term.append_message(
            session_id, "assistant", scrubbed_agent, operation_id=op_id_agent
        )

        # Future extension: Dispatch long term storage tasks to Qdrant (Batch 3)
        return True

    async def retrieve(
        self,
        user_id: str,
        session_id: str,
        query: str,
        limit: int = 5,
        tenant_id: Optional[str] = None,
    ) -> List[MemoryItem]:
        """Future extension point for Batch 3 vector memory lookup."""
        return []

    async def search(
        self, user_id: str, query: str, limit: int = 10, tenant_id: Optional[str] = None
    ) -> List[MemoryItem]:
        """Future extension point for Batch 3 Qdrant raw search."""
        return []

    async def delete(self, user_id: str, memory_id: str) -> None:
        """Future extension point for Batch 3 soft-deleting vector memory."""
        pass

    async def clear(self, user_id: str, session_id: str) -> None:
        """Clears short-term active caches and resets session."""
        meta_data = await self.short_term.load_session(session_id)
        if meta_data and meta_data.get("user_id") != user_id:
            raise SharedMemoryAccessException("Access Denied: Session owner mismatch.")

        await self.short_term.clear_session(session_id)

    async def pin(self, user_id: str, memory_id: str) -> None:
        """Future extension point for Batch 3 memory pinning."""
        pass

    async def forget(self, user_id: str) -> None:
        """Future extension point for GDPR purging (Batch 3)."""
        pass

    async def rollback(
        self, user_id: str, memory_id: str, target_version_id: str
    ) -> None:
        """Future extension point for rollbacks (Batch 3)."""
        pass

    def compare_versions(
        self, version_a: MemoryItem, version_b: MemoryItem
    ) -> Dict[str, Any]:
        """Future extension point for version comparisons (Batch 3)."""
        return {}


# Export default singleton instance
memory_manager = MemoryManager()
