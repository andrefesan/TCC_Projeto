"""Gerenciador de checkpoint para rastreamento de paginação na ingestão."""
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()

DEFAULT_PATH = Path(__file__).parent.parent.parent / "data" / "ingestion_checkpoint.json"


class CheckpointManager:
    """Rastreia progresso de ingestão via arquivo JSON com escrita atômica."""

    def __init__(self, path: Path = DEFAULT_PATH):
        self.path = path
        self.data: dict[str, Any] = self.load()

    def load(self) -> dict[str, Any]:
        """Carrega checkpoint existente ou retorna estrutura vazia."""
        if self.path.exists():
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("checkpoint_corrupto", erro=str(e))
        return {}

    def save(self):
        """Salva checkpoint atomicamente (write .tmp + rename)."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        os.replace(str(tmp), str(self.path))

    def reset(self):
        """Limpa checkpoint para nova execução."""
        self.data = {}
        self.save()

    def _ensure_source(self, source: str):
        if source not in self.data:
            self.data[source] = {}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ---- Status ----

    def get_status(self, source: str, key: str) -> str:
        """Retorna status: 'pending' | 'in_progress' | 'completed'."""
        return self.data.get(source, {}).get(key, {}).get("status", "pending")

    def is_source_completed(self, source: str, keys: list[str]) -> bool:
        """Verifica se todas as chaves de uma fonte estão completas."""
        return all(self.get_status(source, k) == "completed" for k in keys)

    # ---- Marcação ----

    def mark_started(self, source: str, key: str):
        """Marca uma chave como em progresso."""
        self._ensure_source(source)
        if key not in self.data[source]:
            self.data[source][key] = {}
        self.data[source][key].update({
            "status": "in_progress",
            "started_at": self._now(),
        })
        self.save()

    def mark_completed(self, source: str, key: str, total: int):
        """Marca uma chave como concluída."""
        self._ensure_source(source)
        if key not in self.data[source]:
            self.data[source][key] = {}
        self.data[source][key].update({
            "status": "completed",
            "total": total,
            "completed_at": self._now(),
        })
        self.save()
        logger.info("checkpoint_completed", source=source, key=key, total=total)

    def update_progress(self, source: str, key: str, **kwargs):
        """Atualiza progresso parcial (last_page, total, etc.)."""
        self._ensure_source(source)
        if key not in self.data[source]:
            self.data[source][key] = {"status": "in_progress"}
        self.data[source][key].update(kwargs)
        self.save()

    # ---- Leitura ----

    def get_last_page(self, source: str, key: str) -> int:
        """Retorna última página consumida (0 se inexistente)."""
        return self.data.get(source, {}).get(key, {}).get("last_page", 0)

    def get_value(self, source: str, key: str, field: str, default=None):
        """Retorna valor arbitrário do checkpoint."""
        return self.data.get(source, {}).get(key, {}).get(field, default)

    # ---- Resumo ----

    def summary(self) -> dict:
        """Retorna resumo para logging."""
        result = {}
        for source, keys in self.data.items():
            completed = sum(1 for v in keys.values()
                           if isinstance(v, dict) and v.get("status") == "completed")
            total_keys = sum(1 for v in keys.values() if isinstance(v, dict))
            result[source] = f"{completed}/{total_keys}"
        return result


class ProgressTracker:
    """Rastreia progresso com estimativa de tempo restante."""

    def __init__(self, total: int, label: str):
        self.total = total
        self.label = label
        self.processed = 0
        self.start_time = time.monotonic()

    def tick(self, n: int = 1):
        self.processed += n
        elapsed = time.monotonic() - self.start_time
        rate = self.processed / elapsed if elapsed > 0 else 0
        remaining = (self.total - self.processed) / rate if rate > 0 else 0

        if self.processed % max(1, self.total // 20) == 0 or self.processed == self.total:
            logger.info(
                "progresso",
                etapa=self.label,
                processados=self.processed,
                total=self.total,
                percentual=f"{self.processed / self.total * 100:.1f}%",
                taxa_por_seg=round(rate, 2),
                eta_min=round(remaining / 60, 1),
            )
