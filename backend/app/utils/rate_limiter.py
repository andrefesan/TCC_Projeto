import asyncio
import time
from tenacity import retry, wait_exponential, stop_after_attempt
import structlog

logger = structlog.get_logger()


class RateLimiter:
    """Token bucket rate limiter — non-blocking entre chaves diferentes."""

    def __init__(self, requests_per_minute: int = 400):
        self.rpm = requests_per_minute
        self.interval = 60.0 / requests_per_minute
        self._next_allowed = 0.0
        self._lock = asyncio.Lock()
        self.request_count = 0

    async def acquire(self):
        """Reserva slot e espera FORA do lock — libera outras chaves."""
        async with self._lock:
            now = time.monotonic()
            if self._next_allowed <= now:
                self._next_allowed = now + self.interval
                wait = 0.0
            else:
                wait = self._next_allowed - now
                self._next_allowed += self.interval
            self.request_count += 1

        # Sleep fora do lock — outras chaves podem reservar em paralelo
        if wait > 0:
            await asyncio.sleep(wait)

    @staticmethod
    def with_retry(max_attempts: int = 5):
        """Decorator para retry com backoff exponencial."""
        return retry(
            wait=wait_exponential(multiplier=2, min=1, max=60),
            stop=stop_after_attempt(max_attempts),
            reraise=True,
        )
