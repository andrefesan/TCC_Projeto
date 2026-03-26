"""Circuit breaker para proteção contra falhas em cascata na coleta de dados."""
import json
import time
from pathlib import Path
from typing import Any
import structlog

logger = structlog.get_logger()


class CircuitBreaker:
    """Circuit breaker com estados CLOSED → OPEN → HALF_OPEN."""

    def __init__(self, failure_threshold: int = 10, recovery_timeout: float = 300.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.consecutive_failures = 0
        self.state = "CLOSED"
        self.opened_at: float = 0.0

    def record_success(self):
        self.consecutive_failures = 0
        if self.state != "CLOSED":
            logger.info("circuit_breaker_fechado")
            self.state = "CLOSED"

    def record_failure(self):
        self.consecutive_failures += 1
        if self.consecutive_failures >= self.failure_threshold and self.state == "CLOSED":
            self.state = "OPEN"
            self.opened_at = time.monotonic()
            logger.warning("circuit_breaker_aberto",
                           falhas=self.consecutive_failures,
                           recovery_s=self.recovery_timeout)

    def can_proceed(self) -> bool:
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            elapsed = time.monotonic() - self.opened_at
            if elapsed >= self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("circuit_breaker_half_open")
                return True
            return False
        # HALF_OPEN — permite 1 tentativa
        return True


class DeadLetterQueue:
    """Fila de itens que falharam permanentemente."""

    def __init__(self, path: Path):
        self.path = path
        self.items: list[dict] = self._load()

    def _load(self) -> list[dict]:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pass
        return []

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.items, indent=2, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
        import os
        os.replace(str(tmp), str(self.path))

    def add(self, fase: str, identificador: str, erro: str):
        # Verificar se já existe
        for item in self.items:
            if item["fase"] == fase and item["identificador"] == identificador:
                item["retry_count"] = item.get("retry_count", 0) + 1
                item["ultimo_erro"] = erro
                item["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
                self.save()
                return
        self.items.append({
            "fase": fase,
            "identificador": identificador,
            "erro": erro,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "retry_count": 1,
        })
        self.save()

    def get_pending(self, fase: str, max_retries: int = 5) -> list[dict]:
        return [
            item for item in self.items
            if item["fase"] == fase and item.get("retry_count", 0) < max_retries
        ]

    def mark_resolved(self, fase: str, identificador: str):
        self.items = [
            item for item in self.items
            if not (item["fase"] == fase and item["identificador"] == identificador)
        ]
        self.save()

    @property
    def count(self) -> int:
        return len(self.items)

    def summary(self) -> dict[str, int]:
        result: dict[str, int] = {}
        for item in self.items:
            result[item["fase"]] = result.get(item["fase"], 0) + 1
        return result
