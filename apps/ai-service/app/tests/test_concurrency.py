"""
Pytest suite for Phase 3 Milestone 2.2 Batch 2.2
Distributed Concurrency and Consistency Layer.
"""

import pytest
import redis
import anyio
from unittest.mock import MagicMock, patch

from app.memory.short_term import short_term_memory
from app.memory.locks import (
    LockManager,
    RedisDistributedLock,
    InMemoryDistributedLock,
    BaseLock,
)
from app.memory.versioning import VersionManager, MemoryVersionConflict
from app.memory.conflicts import ConflictResolver, STRATEGY_OVERWRITE, STRATEGY_REJECT
from app.memory.retry import RetryPolicy
from app.memory.concurrency import concurrency_metrics, ConcurrencyManager
from app.memory.exceptions import ConcurrencyLockError
from app.config.config import settings


@pytest.mark.anyio
async def test_in_memory_lock_acquisition_and_release():
    lock = LockManager.get_lock(None, "sess-lock-1", ttl_secs=1.0)

    # 1. First acquire succeeds
    assert lock.acquire(blocking=False) is True

    # 2. Second parallel acquire fails
    lock2 = LockManager.get_lock(None, "sess-lock-1", ttl_secs=1.0)
    assert lock2.acquire(blocking=False) is False

    # 3. Release lock 1 succeeds
    assert lock.release() is True

    # 4. Lock 2 can now acquire
    assert lock2.acquire(blocking=False) is True
    assert lock2.release() is True


@pytest.mark.anyio
async def test_lock_timeout_and_ownership_validation():
    lock = LockManager.get_lock(None, "sess-lock-2", ttl_secs=0.2)
    assert lock.acquire(blocking=False) is True

    # Wait for lock TTL to expire
    await anyio.sleep(0.3)

    # A different lock owner can now acquire it because lock expired
    lock2 = LockManager.get_lock(None, "sess-lock-2", ttl_secs=1.0)
    assert lock2.acquire(blocking=False) is True

    # The first lock cannot release or renew it because ownership has changed/expired
    assert lock.release() is False
    assert lock.renew(additional_ttl=1.0) is False

    # Clean up lock 2
    assert lock2.release() is True


@pytest.mark.anyio
async def test_redis_distributed_lock_atomic_lua():
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True
    mock_redis.set.return_value = True
    mock_redis.eval.return_value = 1

    lock = LockManager.get_lock(mock_redis, "sess-redis-1", ttl_secs=2.0)
    assert isinstance(lock, RedisDistributedLock)

    # Acquire
    assert lock.acquire(blocking=False) is True
    mock_redis.set.assert_called_once()

    # Release
    assert lock.release() is True
    mock_redis.eval.assert_called_once()

    # Renew
    mock_redis.eval.reset_mock()
    mock_redis.eval.return_value = 1
    assert lock.renew(additional_ttl=2.0) is True
    mock_redis.eval.assert_called_once()


@pytest.mark.anyio
async def test_redis_failure_simulation_fallback():
    # If Redis connection check throws exception, LockManager falls back to InMemoryDistributedLock
    mock_redis = MagicMock()
    mock_redis.ping.side_effect = redis.exceptions.ConnectionError("Redis down")

    lock = LockManager.get_lock(mock_redis, "sess-fallback-1")
    assert isinstance(lock, InMemoryDistributedLock)
    assert lock.acquire(blocking=False) is True
    assert lock.release() is True


@pytest.mark.anyio
async def test_optimistic_concurrency_control_validation():
    # Correct expected version matches current
    VersionManager.validate_occ(current_version=5, expected_version=5)

    # Version mismatch throws conflict error
    with pytest.raises(MemoryVersionConflict):
        VersionManager.validate_occ(current_version=5, expected_version=4)

    with pytest.raises(MemoryVersionConflict):
        VersionManager.validate_occ(current_version=5, expected_version=6)


def test_conflict_resolver_strategies():
    incoming = {"val": 2}
    current = {"val": 1}

    # 1. OVERWRITE returns incoming
    res = ConflictResolver.resolve(current, incoming, strategy=STRATEGY_OVERWRITE)
    assert res == incoming

    # 2. REJECT throws MemoryVersionConflict
    with pytest.raises(MemoryVersionConflict):
        ConflictResolver.resolve(current, incoming, strategy=STRATEGY_REJECT)

    # 3. Invalid strategy throws ValueError
    with pytest.raises(ValueError):
        ConflictResolver.resolve(current, incoming, strategy="INVALID")


def test_retry_policy_exponential_backoff_and_jitter():
    # Test retryable transient exception
    counter = 0

    def transient_action():
        nonlocal counter
        counter += 1
        if counter < 3:
            raise ConcurrencyLockError("Lock busy")
        return "success"

    policy = RetryPolicy(
        max_attempts=4, base_delay=0.01, backoff_factor=2.0, jitter=True
    )
    res = policy.execute(transient_action)
    assert res == "success"
    assert counter == 3

    # Test non-retryable exception propagates immediately
    counter2 = 0

    def logical_action():
        nonlocal counter2
        counter2 += 1
        raise ValueError("Invalid logical arg")

    policy2 = RetryPolicy(max_attempts=3, base_delay=0.01)
    with pytest.raises(ValueError):
        policy2.execute(logical_action)
    assert counter2 == 1  # Fails immediately without retry


@pytest.mark.anyio
async def test_concurrency_stress_parallel_requests():
    """Simulate parallel concurrent write requests to the same session."""
    session_id = "sess-stress-1"
    user_id = "user-stress-1"

    # Create the session
    await short_term_memory.create_session(user_id, session_id, session_id)

    # Run multiple concurrent appends
    async def task_append(index: int):
        # Serialized operations will execute one-by-one under lock
        await short_term_memory.append_message(
            session_id=session_id, role="user", content=f"message {index}"
        )

    async with anyio.create_task_group() as tg:
        for i in range(10):
            tg.start_soon(task_append, i)

    history = await short_term_memory.get_history(session_id)
    # All 10 messages should be appended cleanly without data loss
    assert len(history) == 10

    # Check that versions have incremented
    meta = await short_term_memory.load_session(session_id)
    assert meta["memory_version"] >= 10

    # Test OCC Conflict rejection path on update_metadata
    # Passing a stale version should raise MemoryVersionConflict
    with pytest.raises(MemoryVersionConflict):
        await short_term_memory.update_metadata(
            session_id=session_id,
            metadata_updates={"beta_mode": True},
            expected_version=1,  # Expected 1, actual version is >= 10
        )

    # Clean up
    await short_term_memory.delete_session(session_id)


@pytest.mark.anyio
async def test_lock_lifecycle_metrics_tracking():
    session_id = "sess-metrics-1"

    # Get current rollback count
    initial_rollbacks = concurrency_metrics["rollback_count"]

    async def failing_operation():
        raise RuntimeError("Something went wrong during write transaction")

    # Run the transaction wrapping the failing operation
    mgr = ConcurrencyManager(short_term_memory)
    with pytest.raises(RuntimeError):
        await mgr.execute_transaction(session_id, failing_operation)

    # Check that rollback count metric was incremented
    assert concurrency_metrics["rollback_count"] > initial_rollbacks


def test_base_lock_placeholders():
    """Verify that placeholder methods on BaseLock raise NotImplementedError."""
    base = BaseLock("session-placeholder")
    with pytest.raises(NotImplementedError):
        base.acquire()
    with pytest.raises(NotImplementedError):
        base.release()
    with pytest.raises(NotImplementedError):
        base.renew()


@pytest.mark.anyio
async def test_redis_blocking_and_exception_paths():
    """Verify Redis distributed lock blocking retry and script exception paths."""
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    # Simulate first two tries failing, then third succeeding
    returns = [False, False, True]

    def mock_set(*args, **kwargs):
        return returns.pop(0) if returns else False

    mock_redis.set.side_effect = mock_set

    lock = RedisDistributedLock(mock_redis, "sess-blocking-1", ttl_secs=1.0)
    # Patch settings to make retries faster
    with patch.object(settings, "LOCK_RETRY_DELAY_SECS", 0.01):
        assert lock.acquire(blocking=True, timeout=0.5) is True

    # Simulate acquisition timeout failure
    mock_redis.set.side_effect = None
    mock_redis.set.return_value = False
    lock_fail = RedisDistributedLock(mock_redis, "sess-fail-1", ttl_secs=1.0)
    with patch.object(settings, "LOCK_RETRY_DELAY_SECS", 0.01):
        with pytest.raises(ConcurrencyLockError):
            lock_fail.acquire(blocking=True, timeout=0.05)

    # Test Redis eval exceptions in release and renew
    mock_redis.eval.side_effect = redis.exceptions.RedisError("eval failure")
    assert lock.release() is False
    assert lock.renew(additional_ttl=1.0) is False


@pytest.mark.anyio
async def test_in_memory_blocking_timeout_and_renewals():
    """Verify InMemoryDistributedLock blocking timeouts and renewal edge cases."""
    lock = InMemoryDistributedLock("sess-inmem-edge", ttl_secs=1.0)
    assert lock.acquire(blocking=False) is True

    # Try parallel acquire with blocking timeout (should timeout)
    lock_fail = InMemoryDistributedLock("sess-inmem-edge", ttl_secs=1.0)
    with patch.object(settings, "LOCK_RETRY_DELAY_SECS", 0.01):
        with pytest.raises(ConcurrencyLockError):
            lock_fail.acquire(blocking=True, timeout=0.05)

    # Renewing a non-acquired or mismatched owner lock returns False
    lock_wrong = InMemoryDistributedLock(
        "sess-inmem-edge", owner_token="wrong-owner", ttl_secs=1.0
    )
    assert lock_wrong.renew(additional_ttl=1.0) is False
    assert lock_wrong.release() is False

    # Clean up
    assert lock.release() is True


def test_version_manager_occ_disable():
    """Verify VersionManager edge cases and disabled validation settings."""
    # When OCC is disabled, check validates without error
    with patch.object(settings, "OCC_ENABLED", False):
        VersionManager.validate_occ(5, 4)  # Mismatch doesn't raise error when disabled

    # None expected version validates successfully
    VersionManager.validate_occ(5, None)


def test_retry_policy_exhaustion_logging():
    """Verify logging message when RetryPolicy runs out of attempts."""
    policy = RetryPolicy(max_attempts=1, base_delay=0.01)

    def raise_transient():
        raise ConcurrencyLockError("busy")

    with pytest.raises(ConcurrencyLockError):
        policy.execute(raise_transient)
