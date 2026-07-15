# app/integration/resiliency/breaker.py
import time
import logging
from typing import Dict
from app.integration.exceptions import ProviderNetworkError

logger = logging.getLogger("ai-service.integration.resiliency.breaker")


class CircuitBreaker:
    def __init__(
        self,
        provider_id: str,
        failure_threshold_percentage: float = 50.0,
        rolling_window_seconds: int = 60,
        reset_timeout_seconds: int = 30,
        min_requests_for_trip: int = 10,
        redis_client=None,
    ):
        self.provider_id = provider_id
        self.failure_threshold = failure_threshold_percentage
        self.rolling_window = rolling_window_seconds
        self.reset_timeout = reset_timeout_seconds
        self.min_requests = min_requests_for_trip
        self.redis_client = redis_client

        # Local in-memory state fallback
        self._local_state = "CLOSED"
        self._local_last_trip_time = 0.0
        self._local_requests = []  # List of timestamps (time, success)

    def _get_redis_keys(self) -> Dict[str, str]:
        base = f"circuit_breaker:{self.provider_id}"
        return {
            "state": f"{base}:state",
            "last_trip": f"{base}:last_trip",
            "requests": f"{base}:requests",
        }

    async def get_state(self) -> str:
        if self.redis_client:
            try:
                keys = self._get_redis_keys()
                state = self.redis_client.get(keys["state"])
                if state:
                    state_str = (
                        state.decode("utf-8")
                        if isinstance(state, bytes)
                        else str(state)
                    )
                    # Check reset timeout if open
                    if state_str == "OPEN":
                        last_trip = self.redis_client.get(keys["last_trip"])
                        last_trip_time = float(last_trip) if last_trip else 0.0
                        if time.time() - last_trip_time > self.reset_timeout:
                            self.redis_client.set(keys["state"], "HALF-OPEN")
                            state_str = "HALF-OPEN"
                    return state_str
            except Exception as e:
                logger.warning(
                    f"Redis circuit breaker get_state failed: {e}. Using in-memory fallback."
                )

        # Local in-memory
        if self._local_state == "OPEN":
            if time.time() - self._local_last_trip_time > self.reset_timeout:
                self._local_state = "HALF-OPEN"
        return self._local_state

    async def check_allow_request(self) -> bool:
        state = await self.get_state()
        if state == "OPEN":
            raise ProviderNetworkError(
                f"Circuit Breaker is OPEN for provider {self.provider_id}"
            )
        return True

    async def record_result(self, success: bool) -> None:
        now = time.time()
        if self.redis_client:
            try:
                keys = self._get_redis_keys()
                state = await self.get_state()

                if state == "HALF-OPEN":
                    if success:
                        self.redis_client.set(keys["state"], "CLOSED")
                        self.redis_client.delete(keys["requests"])
                        logger.info(
                            f"Circuit Breaker CLOSED for provider {self.provider_id}"
                        )
                    else:
                        self.redis_client.set(keys["state"], "OPEN")
                        self.redis_client.set(keys["last_trip"], now)
                        logger.warning(
                            f"Circuit Breaker tripped to OPEN for provider {self.provider_id} (Canary failed)"
                        )
                    return

                # Record request timestamp and outcome
                req_data = f"{now}:{1 if success else 0}"
                self.redis_client.lpush(keys["requests"], req_data)
                self.redis_client.ltrim(keys["requests"], 0, 99)  # Keep last 100
                self.redis_client.expire(keys["requests"], self.rolling_window)

                # Check sliding window failures
                raw_reqs = self.redis_client.lrange(keys["requests"], 0, -1)
                reqs = []
                for r in raw_reqs:
                    r_str = r.decode("utf-8") if isinstance(r, bytes) else str(r)
                    ts, succ = r_str.split(":")
                    if now - float(ts) <= self.rolling_window:
                        reqs.append(int(succ))

                if len(reqs) >= self.min_requests:
                    failures = len(reqs) - sum(reqs)
                    fail_rate = (failures / len(reqs)) * 100
                    if fail_rate >= self.failure_threshold:
                        self.redis_client.set(keys["state"], "OPEN")
                        self.redis_client.set(keys["last_trip"], now)
                        logger.warning(
                            f"Circuit Breaker tripped to OPEN for provider {self.provider_id} (Fail rate: {fail_rate:.1f}%)"
                        )
                return
            except Exception as e:
                logger.warning(
                    f"Redis circuit breaker record_result failed: {e}. Using in-memory fallback."
                )

        # Local in-memory implementation
        state = self._local_state
        if state == "HALF-OPEN":
            if success:
                self._local_state = "CLOSED"
                self._local_requests.clear()
                logger.info(f"Circuit Breaker CLOSED for provider {self.provider_id}")
            else:
                self._local_state = "OPEN"
                self._local_last_trip_time = now
                logger.warning(
                    f"Circuit Breaker tripped to OPEN for provider {self.provider_id} (Canary failed)"
                )
            return

        self._local_requests.append((now, success))
        # Filter window
        self._local_requests = [
            r for r in self._local_requests if now - r[0] <= self.rolling_window
        ]

        if len(self._local_requests) >= self.min_requests:
            failures = sum(1 for r in self._local_requests if not r[1])
            fail_rate = (failures / len(self._local_requests)) * 100
            if fail_rate >= self.failure_threshold:
                self._local_state = "OPEN"
                self._local_last_trip_time = now
                logger.warning(
                    f"Circuit Breaker tripped to OPEN for provider {self.provider_id} (Fail rate: {fail_rate:.1f}%)"
                )
