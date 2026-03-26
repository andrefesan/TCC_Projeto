import asyncio
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.rag.interpreter import QueryInterpreter
from app.services.rag.decomposer import HybridDecomposer
from app.services.rag.synthesizer import ResponseSynthesizer
from app.services.rag.query_planner import QueryPlanner
from app.services.search.hybrid_search import HybridSearchService
from app.services.search.sql_search import SQLSearchService
from app.services.search.vector_search import VectorSearchService
from app.services.cache import query_cache
from app.config import settings
import structlog

logger = structlog.get_logger()


class RAGPipeline:
    """Pipeline completo de RAG Híbrido com planejamento inteligente."""

    def __init__(self):
        self.interpreter = QueryInterpreter()
        self.decomposer = HybridDecomposer()
        self.synthesizer = ResponseSynthesizer()
        self.planner = QueryPlanner()
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

        # Etapa 2: Planejamento + Decomposição em paralelo
        plano, decomposicao = await asyncio.gather(
            self.planner.planejar(consulta, entidades),
            asyncio.to_thread(self.decomposer.decompor, entidades, db),
        )

        # Etapa 3: Recuperação com estratégia do planner
        operacao = decomposicao.get("operacao", "busca")
        filtros_sql = decomposicao["filtros_sql"]
        limit = min(plano.get("limite_sugerido", settings.MAX_RESULTS), settings.MAX_RESULTS_CAP)
        threshold = plano.get("threshold_suficiencia", limit)
        estrategia = None  # Definida apenas para modo híbrido

        if operacao in ("soma", "contagem", "ranking", "media"):
            # Modo de agregação — ignora modo híbrido/sql_puro
            dados = self.sql_search.construir_agregacao(
                filtros_sql, operacao, db, limit
            )
        elif modo == "sql_puro":
            if decomposicao.get("busca_beneficiario") and decomposicao.get("filtro_beneficiario"):
                dados = self.sql_search.buscar_por_beneficiario(
                    decomposicao["filtro_beneficiario"], filtros_sql, db, limit
                )
            else:
                dados = self.sql_search.construir_e_executar(filtros_sql, db, limit)
        elif modo == "vetorial_puro":
            embedding = self.decomposer.embedder.encode(consulta).tolist()
            dados = self.vector_search.buscar(
                {"termo": consulta, "embedding": embedding}, db, limit=limit
            )
        else:  # "hibrido" (padrão)
            # Estratégia adaptativa: usar recomendação do planner,
            # mas forçar RRF para buscas de beneficiário (vetor agrega valor)
            is_beneficiario = decomposicao.get("busca_beneficiario", False)
            planner_strategy = plano.get("estrategia_hibrida", "rrf")

            if is_beneficiario:
                estrategia = "rrf"
            elif planner_strategy == "sql_only":
                estrategia = "sql_first"  # permitir fallback vetorial se SQL falhar
            else:
                estrategia = planner_strategy  # "rrf" ou "sql_first"

            # Gerar embedding da consulta bruta para componente vetorial
            embedding = self.decomposer.embedder.encode(consulta).tolist()
            busca_vetorial = {"termo": consulta, "embedding": embedding}

            dados = self.search.buscar(
                filtros_sql,
                busca_vetorial,
                db,
                limit=limit,
                sufficiency_threshold=threshold,
                busca_beneficiario=is_beneficiario,
                filtro_beneficiario=decomposicao.get("filtro_beneficiario"),
                estrategia=estrategia,
            )

        # Contagem total para completude (apenas para busca, não agregações)
        completude = None
        if operacao == "busca" and dados:
            total_no_banco = self.sql_search.contar_total(filtros_sql, db)
            completude = {
                "total_no_banco": total_no_banco,
                "resultados_exibidos": len(dados),
                "dados_completos": len(dados) >= total_no_banco,
            }

        # Cruzamento com sanções para beneficiários encontrados
        self._enriquecer_com_sancoes(dados, db)

        # Detecção de instituição específica
        instituicao = entidades.get("instituicao")
        tem_beneficiarios = any(d.get("beneficiario_nome") for d in dados)
        tem_sancoes = any(d.get("sancoes") for d in dados)

        # Etapa 4: Síntese com completude e entidades
        resultado = await self.synthesizer.sintetizar(
            consulta, dados, instituicao=instituicao,
            operacao=operacao, tem_sancoes=tem_sancoes,
            completude=completude, entidades=entidades,
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

        # Hint de visualização (determinístico)
        resultado["visualization_hint"] = self._gerar_hint_visualizacao(
            operacao, dados, plano
        )

        latencia = int((time.time() - inicio) * 1000)
        resultado["metadata"] = {
            "latencia_ms": latencia,
            "entidades": entidades,
            "modo": modo,
            "num_resultados": len(dados),
            "estrategia_hibrida": estrategia if modo == "hibrido" else None,
        }

        # Adicionar completude ao metadata
        if completude:
            resultado["metadata"]["total_no_banco"] = completude["total_no_banco"]
            resultado["metadata"]["dados_completos"] = completude["dados_completos"]

        # Log de consulta
        self._registrar_consulta(db, consulta, entidades, resultado)

        logger.info("consulta_processada", consulta=consulta[:50],
                     latencia_ms=latencia, resultados=len(dados),
                     plano=plano.get("tipo_consulta"))

        # Armazenar no cache
        query_cache.set(cache_key, resultado)

        return resultado

    def _gerar_hint_visualizacao(self, operacao: str, dados: list[dict],
                                  plano: dict) -> str | None:
        """Gera hint de visualização baseado no tipo de consulta e dados."""
        if not dados:
            return None
        if operacao == "ranking":
            return "bar"
        if operacao in ("soma", "contagem", "media") and len(dados) == 1:
            return "card"
        if operacao == "busca":
            anos = {d.get("ano") for d in dados if d.get("ano")}
            if len(anos) > 1:
                return "line"
        return "table"

    def _enriquecer_com_sancoes(self, dados: list[dict], db: Session):
        """Cruza beneficiários encontrados com cadastros de sanções."""
        for d in dados:
            cpf_cnpj = d.get("beneficiario_cpf_cnpj")
            if not cpf_cnpj:
                continue
            sancoes = self.sql_search.verificar_sancoes(cpf_cnpj, db)
            if sancoes:
                d["sancoes"] = sancoes

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
