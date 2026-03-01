import pandas as pd
from pathlib import Path
from typing import List
import structlog

logger = structlog.get_logger()


class SIOPImporter:
    """Importador de classificação funcional-programática do SIOP via CSV."""

    def importar_csv(self, caminho: Path) -> List[dict]:
        """Importa arquivo CSV do SIOP e retorna classificações."""
        df = pd.read_csv(caminho, encoding="utf-8", sep=";")
        logger.info("siop_csv_lido", linhas=len(df), colunas=list(df.columns))

        classificacoes = []
        for _, row in df.iterrows():
            classificacoes.append({
                "funcao": str(row.get("CodFuncao", "")).zfill(2),
                "funcao_nome": row.get("Funcao", ""),
                "subfuncao": str(row.get("CodSubfuncao", "")).zfill(3),
                "subfuncao_nome": row.get("Subfuncao", ""),
                "programa": str(row.get("CodPrograma", "")),
                "programa_nome": row.get("Programa", ""),
                "descricao": f"{row.get('Funcao', '')} - {row.get('Subfuncao', '')} - {row.get('Programa', '')}",
            })

        # Deduplicar por combinação funcao+subfuncao+programa
        seen = set()
        unique = []
        for c in classificacoes:
            key = (c["funcao"], c["subfuncao"], c["programa"])
            if key not in seen:
                seen.add(key)
                unique.append(c)

        logger.info("classificacoes_importadas", total=len(unique))
        return unique
