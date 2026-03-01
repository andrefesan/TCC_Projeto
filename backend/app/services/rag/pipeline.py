import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.rag.interpreter import QueryInterpreter
from app.services.rag.decomposer import HybridDecomposer
from app.services.rag.synthesizer import ResponseSynthesizer
from app.services.search.hybrid_search import HybridSearchService
import structlog

logger = structlog.get_logger()


class RAGPipeline:
    """Pipeline completo de RAG Híbrido."""

    def __init__(self):
        self.interpreter = QueryInterpreter()
        self.decomposer = HybridDecomposer()
        self.synthesizer = ResponseSynthesizer()
        self.search = HybridSearchService()

    async def processar(self, consulta: str, db: Session) -> dict:
        """Processa consulta do cidadão e retorna resposta fundamentada."""
        inicio = time.time()

        # Etapa 1: Interpretação
        entidades = await self.interpreter.interpretar(consulta)

        # Etapa 2: Decomposição
        decomposicao = self.decomposer.decompor(entidades, db)

        # Etapa 3: Recuperação híbrida
        dados = self.search.buscar(
            decomposicao["filtros_sql"],
            decomposicao.get("busca_vetorial"),
            db,
        )

        # Etapa 4: Síntese
        resultado = await self.synthesizer.sintetizar(consulta, dados)

        latencia = int((time.time() - inicio) * 1000)
        resultado["metadata"] = {
            "latencia_ms": latencia,
            "entidades": entidades,
            "modo": "hibrido" if decomposicao.get("busca_vetorial") else "sql",
            "num_resultados": len(dados),
        }

        # Log de consulta
        self._registrar_consulta(db, consulta, entidades, resultado)

        logger.info("consulta_processada", consulta=consulta[:50],
                     latencia_ms=latencia, resultados=len(dados))

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
