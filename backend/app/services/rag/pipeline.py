import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.rag.interpreter import QueryInterpreter
from app.services.rag.decomposer import HybridDecomposer
from app.services.rag.synthesizer import ResponseSynthesizer
from app.services.search.hybrid_search import HybridSearchService
from app.services.search.sql_search import SQLSearchService
from app.services.search.vector_search import VectorSearchService
from app.services.cache import query_cache
import structlog

logger = structlog.get_logger()


class RAGPipeline:
    """Pipeline completo de RAG Híbrido."""

    def __init__(self):
        self.interpreter = QueryInterpreter()
        self.decomposer = HybridDecomposer()
        self.synthesizer = ResponseSynthesizer()
        self.search = HybridSearchService()
        self.sql_search = SQLSearchService()
        self.vector_search = VectorSearchService()

    async def processar(self, consulta: str, db: Session, modo: str = "hibrido") -> dict:
        """Processa consulta e retorna resposta fundamentada.

        Args:
            consulta: consulta em linguagem natural
            db: sessão do banco
            modo: "hibrido" (padrão), "sql_puro" ou "vetorial_puro"
        """
        # Verificar cache (chave inclui modo para evitar colisões)
        cache_key = f"{modo}:{consulta}"
        cached = query_cache.get(cache_key)
        if cached is not None:
            cached["metadata"]["cache_hit"] = True
            return cached

        inicio = time.time()

        # Etapa 1: Interpretação
        entidades = await self.interpreter.interpretar(consulta)

        # Etapa 2: Decomposição
        decomposicao = self.decomposer.decompor(entidades, db)

        # Etapa 3: Recuperação com modo explícito
        if modo == "sql_puro":
            if decomposicao.get("busca_beneficiario") and decomposicao.get("filtro_beneficiario"):
                dados = self.sql_search.buscar_por_beneficiario(
                    decomposicao["filtro_beneficiario"], decomposicao["filtros_sql"], db
                )
            else:
                dados = self.sql_search.construir_e_executar(decomposicao["filtros_sql"], db)
        elif modo == "vetorial_puro":
            embedding = self.decomposer.embedder.encode(consulta).tolist()
            dados = self.vector_search.buscar(
                {"termo": consulta, "embedding": embedding}, db, limit=20
            )
        else:  # "hibrido" (padrão)
            dados = self.search.buscar(
                decomposicao["filtros_sql"],
                decomposicao.get("busca_vetorial"),
                db,
                busca_beneficiario=decomposicao.get("busca_beneficiario", False),
                filtro_beneficiario=decomposicao.get("filtro_beneficiario"),
            )

        # Detecção de instituição específica
        instituicao = entidades.get("instituicao")
        tem_beneficiarios = any(d.get("beneficiario_nome") for d in dados)

        # Etapa 4: Síntese
        resultado = await self.synthesizer.sintetizar(
            consulta, dados, instituicao=instituicao
        )

        # Disclaimer contextual
        if instituicao and not tem_beneficiarios:
            resultado["disclaimer"] = (
                f"Os resultados apresentados são uma aproximação por área temática "
                f"e localidade. O sistema não possui dados que confirmem o repasse "
                f"direto à instituição mencionada (\"{instituicao}\"). Para verificar "
                f"transferências específicas, consulte o Transferegov.br "
                f"(convênios) ou o Portal da Transparência (transferências)."
            )
        elif tem_beneficiarios:
            resultado["disclaimer"] = (
                "Os dados de beneficiários foram obtidos via documentos de despesa "
                "vinculados às emendas no Portal da Transparência."
            )
        else:
            resultado["disclaimer"] = None

        latencia = int((time.time() - inicio) * 1000)
        resultado["metadata"] = {
            "latencia_ms": latencia,
            "entidades": entidades,
            "modo": modo,
            "num_resultados": len(dados),
        }

        # Log de consulta
        self._registrar_consulta(db, consulta, entidades, resultado)

        logger.info("consulta_processada", consulta=consulta[:50],
                     latencia_ms=latencia, resultados=len(dados))

        # Armazenar no cache
        query_cache.set(cache_key, resultado)

        return resultado

    def _registrar_consulta(self, db: Session, consulta: str,
                             entidades: dict, resultado: dict):
        """Registra consulta no log de auditoria."""
        try:
            import json
            meta = resultado.get("metadata", {})
            db.execute(text("""
                INSERT INTO consultas_log
                    (consulta_nl, entidades_json, modo_busca, num_resultados,
                     latencia_ms, sucesso)
                VALUES (:consulta, :entidades, :modo, :num, :latencia, :sucesso)
            """), {
                "consulta": consulta,
                "entidades": json.dumps(entidades),
                "modo": meta.get("modo", ""),
                "num": meta.get("num_resultados", 0),
                "latencia": meta.get("latencia_ms", 0),
                "sucesso": True,
            })
            db.commit()
        except Exception as e:
            logger.warning("erro_log_consulta", erro=str(e))
