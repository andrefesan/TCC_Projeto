import asyncio
import time
from tenacity import retry, wait_exponential, stop_after_attempt
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Rate limiter com backoff exponencial para APIs governamentais."""

    def __init__(self, requests_per_minute: int = 400):
        self.rpm = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self.last_request = 0.0
        self.request_count = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_request
            if elapsed < self.interval:
                wait = self.interval - elapsed
                logger.debug("rate_limited", wait_ms=round(wait * 1000))
                await asyncio.sleep(wait)
            self.last_request = time.monotonic()
            self.request_count += 1

    @staticmethod
    def with_retry(max_attempts: int = 5):
        """Decorator para retry com backoff exponencial."""
        return retry(
            wait=wait_exponential(multiplier=2, min=1, max=60),
            stop=stop_after_attempt(max_attempts),
            reraise=True,
        )
