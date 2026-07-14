"""
Comprehensive pytest suite for Phase 3 Milestone 2.2 Batch 2.1
Enterprise Short-Term Memory Engine.
"""

import time
import pytest
import redis
from unittest.mock import MagicMock, patch

from app.memory.short_term import (
    short_term_memory,
    memory_manager,
    RedisShortTermMemory,
)
from app.memory.serializer import MemorySerializer
from app.memory.session import (
    STATE_CREATED,
    STATE_ACTIVE,
    STATE_LOCKED,
    STATE_DELETED,
    ConversationSessionMetadata,
    ConversationSessionManager,
)
from app.memory.ttl import TTLEngine
from app.memory.cache import count_tokens, MemoryCachePolicy
from app.memory.exceptions import (
    SharedMemoryAccessException,
    MemoryQuotaExceededException,
)
from app.memory.interfaces import ConversationSession, MemoryItem


@pytest.mark.anyio
async def test_session_creation_and_loading():
    user_id = "traveler-100"
    session_id = "sess-100"
    conv_id = "conv-100"

    # 1. Create session
    meta = await short_term_memory.create_session(
        user_id=user_id,
        session_id=session_id,
        conversation_id=conv_id,
        feature_flags={"beta_routing": True},
    )

    assert meta["user_id"] == user_id
    assert meta["session_id"] == session_id
    assert meta["conversation_id"] == conv_id
    assert meta["session_state"] == STATE_CREATED
    assert meta["feature_flags"]["beta_routing"] is True

    # 2. Check existence
    exists = await short_term_memory.session_exists(session_id)
    assert exists is True

    # 3. Load session
    loaded_meta = await short_term_memory.load_session(session_id)
    assert loaded_meta is not None
    assert loaded_meta["session_id"] == session_id

    # Clean up
    await short_term_memory.delete_session(session_id)


@pytest.mark.anyio
async def test_message_append_and_history():
    user_id = "traveler-200"
    session_id = "sess-200"

    await short_term_memory.create_session(user_id, session_id, session_id)

    # Append message
    success = await short_term_memory.append_message(
        session_id=session_id,
        role="user",
        content="I need a ticket to BPL",
        operation_id="op-unique-123",
    )
    assert success is True

    # Verify idempotency
    success_duplicate = await short_term_memory.append_message(
        session_id=session_id,
        role="user",
        content="I need a ticket to BPL",
        operation_id="op-unique-123",
    )
    assert success_duplicate is True  # Ignored duplicate safely

    history = await short_term_memory.get_history(session_id)
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "I need a ticket to BPL"

    # Clean up
    await short_term_memory.delete_session(session_id)


@pytest.mark.anyio
async def test_cache_eviction_and_max_sessions():
    user_id = "traveler-300"

    # Create 6 sessions (limit is 5)
    for i in range(6):
        session_id = f"sess-300-{i}"
        await short_term_memory.create_session(user_id, session_id, session_id)

    active_sessions = await short_term_memory.list_sessions(user_id)
    # The first session (sess-300-0) should have been evicted automatically
    assert len(active_sessions) == 5
    assert "sess-300-0" not in active_sessions

    # Clean up
    for i in range(1, 6):
        await short_term_memory.delete_session(f"sess-300-{i}")


@pytest.mark.anyio
async def test_state_machine_transitions():
    meta = ConversationSessionManager.create_metadata(
        user_id="user-400", session_id="sess-400", conversation_id="conv-400"
    )
    assert meta.session_state == STATE_CREATED

    # Transition to same state should return without error
    ConversationSessionManager.transition_state(meta, STATE_CREATED)
    assert meta.session_state == STATE_CREATED

    # Valid transition: CREATED -> ACTIVE
    ConversationSessionManager.transition_state(meta, STATE_ACTIVE)
    assert meta.session_state == STATE_ACTIVE

    # Invalid transition: ACTIVE -> CREATED (should fail)
    with pytest.raises(ValueError):
        ConversationSessionManager.transition_state(meta, STATE_CREATED)

    # Valid transition: ACTIVE -> LOCKED
    ConversationSessionManager.transition_state(meta, STATE_LOCKED)
    assert meta.session_state == STATE_LOCKED

    # Valid transition: LOCKED -> ACTIVE
    ConversationSessionManager.transition_state(meta, STATE_ACTIVE)
    assert meta.session_state == STATE_ACTIVE

    # Valid transition: ACTIVE -> DELETED
    ConversationSessionManager.transition_state(meta, STATE_DELETED)
    assert meta.session_state == STATE_DELETED


def test_serializer_pydantic_compatibility():
    session = ConversationSession(
        session_id="sess-500",
        user_id="user-500",
        history=[{"role": "user", "content": "hello"}],
        context={"pref": "window"},
    )

    # Serialize BaseModel
    serialized = MemorySerializer.serialize(session)
    assert isinstance(serialized, str)
    assert "sess-500" in serialized

    # Deserialize BaseModel
    deserialized = MemorySerializer.deserialize(serialized, ConversationSession)
    assert deserialized.session_id == "sess-500"
    assert deserialized.history[0]["content"] == "hello"

    # Serialize/Deserialize normal dictionary
    data_dict = {"foo": "bar"}
    serialized_dict = MemorySerializer.serialize(data_dict)
    assert '{"foo": "bar"}' in serialized_dict
    deserialized_dict = MemorySerializer.deserialize(serialized_dict, dict)
    assert deserialized_dict["foo"] == "bar"


def test_ttl_calculations():
    meta = ConversationSessionMetadata(
        user_id="user-600",
        session_id="sess-600",
        conversation_id="conv-600",
        ttl=10,  # 10 seconds TTL
    )

    # Not expired yet
    assert TTLEngine.is_expired(meta) is False
    assert TTLEngine.is_expired(meta, absolute=True) is False

    # Fast-forward sliding
    meta.last_access = time.time() - 15
    assert TTLEngine.is_expired(meta) is True

    # Fast-forward absolute
    meta.created_at = time.time() - 15
    assert TTLEngine.is_expired(meta, absolute=True) is True

    # Refresh
    TTLEngine.refresh(meta)
    assert TTLEngine.is_expired(meta) is False

    # Reserved extension point
    TTLEngine.run_cleanup_extension_point()


@pytest.mark.anyio
async def test_memory_manager_scrubbing_and_security():
    user_id = "user-700"
    session_id = "sess-700"

    # Save interaction with PII
    await memory_manager.save_interaction(
        user_id=user_id,
        session_id=session_id,
        user_message="My phone is 9999999999 and email is traveler@example.com",
        agent_response="Sure! Tracking PNR 1234567890",
    )

    history = await short_term_memory.get_history(session_id)
    assert len(history) == 2

    # Check that PII was scrubbed
    user_msg_scrubbed = history[0]["content"]
    agent_msg_scrubbed = history[1]["content"]

    assert "9999999999" not in user_msg_scrubbed
    assert "traveler@example.com" not in user_msg_scrubbed
    assert "[PHONE]" in user_msg_scrubbed or "[PNR]" in user_msg_scrubbed
    assert "[EMAIL]" in user_msg_scrubbed

    assert "1234567890" not in agent_msg_scrubbed
    assert "[PNR]" in agent_msg_scrubbed or "[PHONE]" in agent_msg_scrubbed

    # Test cross-user security access violations
    with pytest.raises(SharedMemoryAccessException):
        await memory_manager.save_interaction(
            user_id="unauthorized-user-800",
            session_id=session_id,
            user_message="hello",
            agent_response="hi",
        )

    # Clean up
    await short_term_memory.delete_session(session_id)


@pytest.mark.anyio
async def test_redis_active_paths():
    """Verify primary Redis storage paths by mocking the Redis client."""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    # Mock storage dictionary
    storage = {}

    def mock_set(key, val, *args, **kwargs):
        storage[key] = val
        return True

    def mock_get(key):
        return storage.get(key)

    def mock_exists(key):
        return key in storage

    def mock_delete(*keys):
        for k in keys:
            storage.pop(k, None)

    mock_redis.set.side_effect = mock_set
    mock_redis.get.side_effect = mock_get
    mock_redis.exists.side_effect = mock_exists
    mock_redis.delete.side_effect = mock_delete
    mock_redis.sadd.return_value = 1
    mock_redis.smembers.return_value = {b"sess-redis-123"}
    mock_redis.srem.return_value = 1
    mock_redis.expire.return_value = True

    # Use patch to inject the mock client
    with patch.object(short_term_memory, "redis_client", mock_redis):
        assert short_term_memory._is_redis_active() is True

        # Test session creation
        await short_term_memory.create_session(
            "user-redis", "sess-redis-123", "conv-redis"
        )
        exists = await short_term_memory.session_exists("sess-redis-123")
        assert exists is True

        # Test load session
        meta = await short_term_memory.load_session("sess-redis-123")
        assert meta is not None
        assert meta["user_id"] == "user-redis"

        # Test append message
        await short_term_memory.append_message("sess-redis-123", "user", "redis query")
        history = await short_term_memory.get_history("sess-redis-123")
        assert len(history) == 1
        assert history[0]["content"] == "redis query"

        # Test update metadata
        await short_term_memory.update_metadata("sess-redis-123", {"new_flag": "yes"})

        # Test save conversation
        await short_term_memory.save_conversation(
            "sess-redis-123", {"history": [{"role": "user", "content": "direct"}]}
        )

        # Test list sessions
        sessions = await short_term_memory.list_sessions("user-redis")
        assert "sess-redis-123" in sessions

        # Test delete session
        await short_term_memory.delete_session("sess-redis-123")


@pytest.mark.anyio
async def test_redis_failure_fallback_blocks():
    """Verify that Redis connection failures fallback to local store properly."""
    mock_redis = MagicMock()
    mock_redis.ping.side_effect = redis.exceptions.ConnectionError("Redis offline")
    mock_redis.get.side_effect = redis.exceptions.ConnectionError("Redis offline")
    mock_redis.set.side_effect = redis.exceptions.ConnectionError("Redis offline")
    mock_redis.exists.side_effect = redis.exceptions.ConnectionError("Redis offline")
    mock_redis.delete.side_effect = redis.exceptions.ConnectionError("Redis offline")
    mock_redis.smembers.side_effect = redis.exceptions.ConnectionError("Redis offline")

    with patch.object(short_term_memory, "redis_client", mock_redis):
        # Even with client present, it fails ping and returns False
        assert short_term_memory._is_redis_active() is False

        # Facade methods fall back to memory store and complete without crashing
        await short_term_memory.create_session(
            "user-fail", "sess-fail-123", "conv-fail"
        )
        exists = await short_term_memory.session_exists("sess-fail-123")
        assert exists is True

        meta = await short_term_memory.load_session("sess-fail-123")
        assert meta is not None

        await short_term_memory.append_message("sess-fail-123", "user", "fail query")
        history = await short_term_memory.get_history("sess-fail-123")
        assert len(history) == 1

        await short_term_memory.update_metadata("sess-fail-123", {"beta": "no"})
        await short_term_memory.delete_session("sess-fail-123")


@pytest.mark.anyio
async def test_memory_manager_placeholders_and_exceptions():
    """Verify that placeholder methods in MemoryManager run without errors."""
    mgr = memory_manager

    # 1. Retrieve
    res_ret = await mgr.retrieve("user-900", "sess-900", "hello")
    assert res_ret == []

    # 2. Search
    res_search = await mgr.search("user-900", "hello")
    assert res_search == []

    # 3. Delete
    await mgr.delete("user-900", "mem-900")

    # 4. Pin
    await mgr.pin("user-900", "mem-900")

    # 5. Forget
    await mgr.forget("user-900")

    # 6. Rollback
    await mgr.rollback("user-900", "mem-900", "ver-900")

    # 7. Compare versions
    item_a = MemoryItem(
        id="mem-1",
        user_id="u",
        session_id="s",
        text="a",
        version_id="v1",
        schema_version=1,
    )
    res_comp = mgr.compare_versions(item_a, item_a)
    assert res_comp == {}

    # Test payload size limit check
    with pytest.raises(MemoryQuotaExceededException):
        large_content = "X" * (501 * 1024)  # Exceeds 500KB
        await short_term_memory.create_session("user-900", "sess-large", "conv-large")
        await short_term_memory.save_session_context(
            "sess-large", {"large_context": large_content}
        )

    # Clear manager session
    await short_term_memory.create_session("user-clear", "sess-clear", "conv-clear")
    await mgr.clear("user-clear", "sess-clear")
    exists = await short_term_memory.session_exists("sess-clear")
    assert exists is False

    # Security check on manager clear
    await short_term_memory.create_session(
        "user-clear-owner", "sess-clear-owner", "conv-clear-owner"
    )
    with pytest.raises(SharedMemoryAccessException):
        await mgr.clear("wrong-user", "sess-clear-owner")
    await short_term_memory.delete_session("sess-clear-owner")


def test_fifo_eviction_and_utilities():
    policy = MemoryCachePolicy(max_sessions=2, policy="FIFO")
    policy.record_access("user-1", "sess-1")
    policy.record_access("user-1", "sess-2")

    # Adding a third session should evict the first (FIFO)
    evicted = policy.evict_if_needed("user-1", "sess-3")
    assert evicted == ["sess-1"]

    policy_lru = MemoryCachePolicy(max_sessions=2, policy="LRU")
    policy_lru.record_access("user-1", "sess-1")
    policy_lru.record_access("user-1", "sess-2")
    # Touch sess-1 to make sess-2 the LRU victim
    policy_lru.record_access("user-1", "sess-1")
    evicted_lru = policy_lru.evict_if_needed("user-1", "sess-3")
    assert evicted_lru == ["sess-2"]

    # Remove non-existent user/session queue removals
    policy.remove_session("user-none", "sess-none")
    assert count_tokens("hello world") == 3


def test_fallback_store_direct_coverage():
    """Verify in-memory fallback direct method calls for full coverage."""
    store = short_term_memory.fallback_store

    assert store.exists("sess-direct-none") is False
    assert store.get_session("sess-direct-none") is None
    assert store.get_meta("sess-direct-none") is None
    assert store.list_sessions("user-direct-none") == []

    store.save_session("user-direct", "sess-direct", "session_json", "meta_json")
    assert store.exists("sess-direct") is True
    assert store.get_session("sess-direct") == "session_json"
    assert store.get_meta("sess-direct") == "meta_json"
    assert "sess-direct" in store.list_sessions("user-direct")

    store.delete_session("user-direct", "sess-direct")
    assert store.exists("sess-direct") is False


def test_redis_memory_engine_direct_coverage():
    """Verify RedisShortTermMemory helper methods directly with mock client."""
    mock_cli = MagicMock()
    engine = RedisShortTermMemory(mock_cli)

    mock_cli.exists.return_value = True
    assert engine.exists("sess") is True

    mock_cli.get.return_value = b"raw_bytes"
    assert engine.get_session("user", "sess") == "raw_bytes"
    assert engine.get_meta("sess") == "raw_bytes"


@pytest.mark.anyio
async def test_specific_line_coverages():
    """Test explicit edge cases to cover missing lines in short_term.py."""
    # Test Redis successful initialization logging
    original_client = short_term_memory.redis_client
    try:
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        with patch("redis.Redis.from_url", return_value=mock_redis):
            short_term_memory._init_redis()
            assert short_term_memory.redis_client is not None
    finally:
        short_term_memory.redis_client = original_client

    # Test save_session_context with a brand-new session
    new_sess_id = "sess-brand-new"
    await short_term_memory.save_session_context(new_sess_id, {"page": "home"})
    ctx = await short_term_memory.get_session_context(new_sess_id)
    assert ctx["page"] == "home"

    # Test get_session_context when metadata is missing
    assert await short_term_memory.get_session_context("non-existent-sess") == {}

    # Test get_history when metadata is missing
    assert await short_term_memory.get_history("non-existent-sess") == []

    # Test get_history when session itself is missing but metadata exists (corrupted state)
    # We write metadata but delete session directly from backing store
    await short_term_memory.create_session("user-corr", "sess-corr", "conv-corr")
    short_term_memory.fallback_store._sessions.pop("sess-corr", None)
    assert await short_term_memory.get_history("sess-corr") == []

    # Test session_exists when session has expired
    await short_term_memory.create_session("user-exp", "sess-exp", "conv-exp")
    meta = await short_term_memory._get_meta_obj("sess-exp")
    meta.last_access = time.time() - 90000  # Make it expired
    # Save back directly
    short_term_memory.fallback_store._meta["sess-exp"] = MemorySerializer.serialize(
        meta
    )
    assert await short_term_memory.session_exists("sess-exp") is False

    # Test append_message when session has expired
    await short_term_memory.create_session("user-exp2", "sess-exp2", "conv-exp2")
    meta2 = await short_term_memory._get_meta_obj("sess-exp2")
    meta2.last_access = time.time() - 90000
    short_term_memory.fallback_store._meta["sess-exp2"] = MemorySerializer.serialize(
        meta2
    )
    with pytest.raises(KeyError):
        await short_term_memory.append_message("sess-exp2", "user", "hi")

    # Test append_message when session data is missing (corrupted)
    await short_term_memory.create_session("user-corr2", "sess-corr2", "conv-corr2")
    short_term_memory.fallback_store._sessions.pop("sess-corr2", None)
    with pytest.raises(KeyError):
        await short_term_memory.append_message("sess-corr2", "user", "hi")

    # Test update_metadata when session doesn't exist
    with pytest.raises(KeyError):
        await short_term_memory.update_metadata("non-existent-sess", {"flag": "1"})

    # Test save_conversation when session doesn't exist
    with pytest.raises(KeyError):
        await short_term_memory.save_conversation("non-existent-sess", {"history": []})

    # Test delete_session when metadata doesn't exist
    await short_term_memory.delete_session("non-existent-sess")

    # Clean up remaining sessions
    await short_term_memory.delete_session("sess-brand-new")
    await short_term_memory.delete_session("sess-corr")
    await short_term_memory.delete_session("sess-corr2")
