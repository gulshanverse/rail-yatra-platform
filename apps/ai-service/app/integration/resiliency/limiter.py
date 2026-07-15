# app/integration/resiliency/limiter.py
import time
import logging
from typing import Dict, Tuple
from app.integration.interfaces import IRateLimiter
from app.integration.exceptions import ProviderRateLimitError

logger = logging.getLogger("ai-service.integration.resiliency.limiter")


class TokenBucketRateLimiter(IRateLimiter):
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        # In-memory fallback if Redis is not configured
        self._local_buckets: Dict[
            str, Tuple[float, float]
        ] = {}  # key -> (tokens, last_update)
        self._daily_usage: Dict[
            str, Tuple[int, str]
        ] = {}  # key -> (count, date_string)

    def _get_date_str(self) -> str:
        return time.strftime("%Y-%m-%d", time.gmtime())

    async def check_rate_limit(self, provider_id: str, capability: str) -> bool:
        # Use mock configuration values from settings or registry
        # Typically limits are: 60 rpm, 100 burst, 10000 daily
        rpm = 60
        burst = 100
        daily_limit = 10000

        key = f"rate_limit:{provider_id}:{capability}"
        now = time.time()

        if self.redis_client:
            try:
                # Redis token bucket
                pipe = self.redis_client.pipeline()
                bucket_key = f"tokens:{key}"
                last_update_key = f"last_update:{key}"

                # Check daily quota first
                daily_key = f"quota:daily:{provider_id}:{self._get_date_str()}"
                quota = self.redis_client.get(daily_key)
                if quota and int(quota) >= daily_limit:
                    raise ProviderRateLimitError(
                        f"Daily quota of {daily_limit} exceeded for {provider_id}"
                    )

                # Refresh bucket
                res = self.redis_client.mget([bucket_key, last_update_key])
                curr_tokens = float(res[0]) if res[0] is not None else float(burst)
                last_update = float(res[1]) if res[1] is not None else now

                # Add new tokens
                elapsed = now - last_update
                refill_rate = rpm / 60.0  # tokens per second
                new_tokens = min(float(burst), curr_tokens + (elapsed * refill_rate))

                if new_tokens < 1.0:
                    raise ProviderRateLimitError(
                        f"Rate limit exceeded for provider {provider_id} capability {capability}"
                    )

                new_tokens -= 1.0
                pipe.set(bucket_key, new_tokens)
                pipe.set(last_update_key, now)
                pipe.incr(daily_key)
                pipe.execute()
                return True
            except ProviderRateLimitError:
                raise
            except Exception as e:
                logger.warning(
                    f"Redis rate limiter error: {e}. Falling back to in-memory limiter."
                )

        # Local in-memory fallback
        # 1. Daily Quota Check
        date_str = self._get_date_str()
        daily_key = f"{provider_id}:{date_str}"
        curr_count, last_date = self._daily_usage.get(daily_key, (0, date_str))
        if last_date != date_str:
            curr_count = 0
            self._daily_usage[daily_key] = (0, date_str)
        if curr_count >= daily_limit:
            raise ProviderRateLimitError(
                f"Daily quota of {daily_limit} exceeded for {provider_id}"
            )

        # 2. Token Bucket
        curr_tokens, last_update = self._local_buckets.get(key, (float(burst), now))
        elapsed = now - last_update
        refill_rate = rpm / 60.0
        new_tokens = min(float(burst), curr_tokens + (elapsed * refill_rate))

        if new_tokens < 1.0:
            raise ProviderRateLimitError(
                f"Rate limit exceeded for provider {provider_id} capability {capability}"
            )

        new_tokens -= 1.0
        self._local_buckets[key] = (new_tokens, now)
        self._daily_usage[daily_key] = (curr_count + 1, date_str)
        return True
