from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.services.rag.dictionary import BudgetDictionary
import structlog

logger = structlog.get_logger()


class HybridDecomposer:
    """Decompõe entidades em filtros SQL + busca vetorial."""

    def __init__(self):
        self.dicionario = BudgetDictionary()
        self._embedder = None

    @property
    def embedder(self):
        if self._embedder is None:
            from sentence_transformers import SentenceTransformer
            logger.info("carregando_modelo_embeddings", model=settings.EMBEDDING_MODEL)
            self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
        return self._embedder

    def decompor(self, entidades: dict, db: Session) -> dict:
        """Retorna filtros SQL e parâmetros de busca vetorial."""
        filtros_sql = {}
        busca_vetorial = None

        # Campos diretamente mapeáveis para SQL
        if entidades.get("ano"):
            filtros_sql["ano"] = int(entidades["ano"])
        if entidades.get("ano_inicio") and entidades.get("ano_fim"):
            filtros_sql["ano_inicio"] = int(entidades["ano_inicio"])
            filtros_sql["ano_fim"] = int(entidades["ano_fim"])
        if entidades.get("uf"):
            uf = self._resolver_uf(entidades["uf"])
            if isinstance(uf, list):
                filtros_sql["ufs"] = uf
            else:
                filtros_sql["uf"] = uf
        if entidades.get("autor"):
            filtros_sql["autor"] = entidades["autor"].upper()
        if entidades.get("partido"):
            filtros_sql["partido"] = entidades["partido"].upper()
        if entidades.get("tipo_emenda"):
            filtros_sql["tipo_emenda"] = entidades["tipo_emenda"]

        # Campo semântico: dicionário → SQL, fallback → busca vetorial
        if entidades.get("area"):
            area = entidades["area"].lower().strip()
            codigo = self.dicionario.resolver_area(area)
            if codigo:
                if len(codigo) <= 2:
                    filtros_sql["funcao"] = codigo
                else:
                    filtros_sql["subfuncao"] = codigo
                logger.info("area_resolvida_dicionario", area=area, codigo=codigo)
            else:
                # Fallback: busca vetorial na classificação orçamentária
                embedding = self.embedder.encode(area)
                codigo = self._busca_vetorial_classificacao(embedding, db)
                if codigo:
                    filtros_sql["funcao"] = codigo
                    logger.info("area_resolvida_vetorial", area=area, codigo=codigo)
                else:
                    busca_vetorial = {"termo": area, "embedding": embedding.tolist()}
                    logger.warning("area_nao_resolvida", area=area)

        return {
            "filtros_sql": filtros_sql,
            "busca_vetorial": busca_vetorial,
            "operacao": entidades.get("operacao", "busca"),
        }

    def _resolver_uf(self, uf_raw: str) -> str | list:
        """Resolve UF ou região para sigla(s)."""
        regioes = self.dicionario.resolver_regiao(uf_raw)
        if regioes:
            return regioes
        return uf_raw.upper()[:2]

    def _busca_vetorial_classificacao(self, embedding, db: Session) -> str | None:
        """Busca classificação mais similar por embedding."""
        result = db.execute(text("""
            SELECT funcao, 1 - (embedding <=> :emb::vector) AS similaridade
            FROM classificacao_orcamentaria
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :emb::vector
            LIMIT 1
        """), {"emb": str(embedding.tolist())})
        row = result.fetchone()
        if row and row.similaridade >= settings.SIMILARITY_THRESHOLD:
            return row.funcao
        return None
