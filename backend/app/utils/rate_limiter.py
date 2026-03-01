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
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_request
            if elapsed < self.interval:
                await asyncio.sleep(self.interval - elapsed)
            self.last_request = time.monotonic()

    @staticmethod
    def with_retry(max_attempts: int = 5):
        """Decorator para retry com backoff exponencial."""
        return retry(
            wait=wait_exponential(multiplier=2, min=1, max=60),
            stop=stop_after_attempt(max_attempts),
            reraise=True,
        )
