"""Cache LRU para consultas frequentes, reduzindo latência e custo de API."""
import hashlib
import time
from collections import OrderedDict
from typing import Any
import structlog

logger = structlog.get_logger()


class QueryCache:
    """Cache em memória com TTL e LRU eviction."""

    def __init__(self, max_size: int = 256, ttl_seconds: int = 3600):
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._hits = 0
        self._misses = 0

    def _make_key(self, consulta: str) -> str:
        """Gera chave normalizada a partir da consulta."""
        normalized = consulta.strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def get(self, consulta: str) -> Any | None:
        """Busca resultado no cache. Retorna None se não encontrado ou expirado."""
        key = self._make_key(consulta)
        if key not in self._cache:
            self._misses += 1
            return None

        timestamp, value = self._cache[key]
        if time.time() - timestamp > self._ttl:
            del self._cache[key]
            self._misses += 1
            logger.debug("cache_expirado", key=key)
            return None

        # Move para o final (mais recente)
        self._cache.move_to_end(key)
        self._hits += 1
        logger.info("cache_hit", key=key, hits=self._hits, misses=self._misses)
        return value

    def set(self, consulta: str, value: Any) -> None:
        """Armazena resultado no cache."""
        key = self._make_key(consulta)

        if key in self._cache:
            self._cache.move_to_end(key)
        elif len(self._cache) >= self._max_size:
            self._cache.popitem(last=False)
            logger.debug("cache_eviction", max_size=self._max_size)

        self._cache[key] = (time.time(), value)

    def stats(self) -> dict:
        """Retorna estatísticas do cache."""
        total = self._hits + self._misses
        return {
            "size": len(self._cache),
            "max_size": self._max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": self._hits / total if total > 0 else 0,
        }

    def clear(self) -> None:
        """Limpa o cache."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0


# Instância global do cache
query_cache = QueryCache()
