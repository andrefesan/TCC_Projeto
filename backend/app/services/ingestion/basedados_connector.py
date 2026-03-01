"""Conector para Base dos Dados (basedosdados.org).

Este módulo é um stub para futura integração com o BigQuery da Base dos Dados.
Para o MVP, os dados são importados via CSV/JSON pré-baixados.
"""
import json
from pathlib import Path
from typing import List
import structlog

logger = structlog.get_logger()


class BaseDadosConnector:
    """Conector para importação de dados da Base dos Dados."""

    def importar_json_local(self, caminho: Path) -> List[dict]:
        """Importa dados de arquivo JSON local (pré-baixado da Base dos Dados)."""
        with open(caminho, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("basedados_json_importado", registros=len(data), arquivo=str(caminho))
        return data
