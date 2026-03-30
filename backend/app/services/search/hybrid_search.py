from sqlalchemy.orm import Session
from typing import List, Optional
from app.services.search.sql_search import SQLSearchService
from app.services.search.vector_search import VectorSearchService
from app.config import settings
import structlog

logger = structlog.get_logger()


class HybridSearchService:
    """Combina busca SQL estruturada com busca vetorial semântica.

    Suporta três estratégias de combinação:
    - "rrf": Reciprocal Rank Fusion (Cormack et al., 2009) — executa ambos
      os sistemas e fusiona rankings. Documentos que aparecem em ambos os
      rankings recebem score maior.
    - "sql_first": SQL prioritário com vetor como complemento — executa
      vetor apenas se SQL retorna resultados insuficientes, mas aplica RRF
      na fusão (em vez de simples concatenação).
    - "sql_only": Apenas SQL, sem busca vetorial.
    """

    def __init__(self):
        self.sql_search = SQLSearchService()
        self.vector_search = VectorSearchService()

    def _fusionar_rrf(self, dados_sql: List[dict], dados_vetoriais: List[dict],
                      limit: int) -> List[dict]:
        """Fusão ponderada por Reciprocal Rank Fusion (Cormack et al., 2009).

        RRF(d) = w_sql / (k + rank_sql(d)) + w_vec / (k + rank_vec(d))

        Extensão com pesos assimétricos (w_sql > w_vec) para preservar
        a cobertura do SQL enquanto permite ao vetor promover documentos
        semanticamente relevantes. Resultados vetoriais abaixo do gate
        de similaridade são filtrados antes da fusão para evitar ruído.
        """
        k = settings.RRF_K
        w_sql = settings.RRF_WEIGHT_SQL
        w_vec = settings.RRF_WEIGHT_VECTOR
        sim_gate = settings.RRF_SIMILARITY_GATE

        # Filtrar resultados vetoriais pelo gate de similaridade
        vetoriais_filtrados = [
            d for d in dados_vetoriais
            if d.get("similaridade", 1.0) >= sim_gate
        ]

        all_docs = {}
        scores = {}

        for rank, d in enumerate(dados_sql):
            doc_id = d["id"]
            all_docs[doc_id] = d
            scores[doc_id] = scores.get(doc_id, 0) + w_sql / (k + rank + 1)

        for rank, d in enumerate(vetoriais_filtrados):
            doc_id = d["id"]
            if doc_id not in all_docs:
                all_docs[doc_id] = d
            elif "doc_observacao" in d and "doc_observacao" not in all_docs[doc_id]:
                all_docs[doc_id]["doc_observacao"] = d["doc_observacao"]
            scores[doc_id] = scores.get(doc_id, 0) + w_vec / (k + rank + 1)

        ranked_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)

        ids_sql = set(d["id"] for d in dados_sql)
        ids_vec = set(d["id"] for d in vetoriais_filtrados)
        overlap = len(ids_sql & ids_vec)

        logger.info("rrf_fusao",
                     sql_candidatos=len(dados_sql),
                     vetorial_brutos=len(dados_vetoriais),
                     vetorial_apos_gate=len(vetoriais_filtrados),
                     overlap=overlap,
                     total_unicos=len(ranked_ids),
                     w_sql=w_sql, w_vec=w_vec, sim_gate=sim_gate)

        result = []
        for doc_id in ranked_ids[:limit]:
            doc = dict(all_docs[doc_id])
            doc["rrf_score"] = scores[doc_id]
            result.append(doc)

        return result

    def buscar(self, filtros_sql: dict, busca_vetorial: Optional[dict],
               db: Session, limit: int = 20,
               sufficiency_threshold: Optional[int] = None,
               busca_beneficiario: bool = False,
               filtro_beneficiario: Optional[str] = None,
               estrategia: str = "rrf",
               buscar_documentos: bool = False) -> List[dict]:
        """Executa busca híbrida com estratégia configurável.

        Args:
            filtros_sql: filtros estruturados para SQL
            busca_vetorial: dict com "termo" e "embedding" (ou None)
            db: sessão do banco
            limit: máximo de resultados
            sufficiency_threshold: mínimo de resultados SQL para considerar suficiente
                (usado apenas na estratégia "sql_first")
            busca_beneficiario: se deve buscar nas tabelas de beneficiários
            filtro_beneficiario: nome do beneficiário para filtrar
            estrategia: "rrf" (fusão completa), "sql_first" (SQL prioritário),
                "sql_only" (apenas SQL)
            buscar_documentos: se deve buscar em documentos_emenda.embedding
                (observações de obras/projetos)

        Returns:
            Lista de dicts com resultados combinados
        """
        # Se há filtro de beneficiário, prioriza busca por beneficiário
        if busca_beneficiario and filtro_beneficiario:
            dados_benef = self.sql_search.buscar_por_beneficiario(
                filtro_beneficiario, filtros_sql, db, limit
            )
            if dados_benef:
                logger.info("busca_beneficiario", resultados=len(dados_benef))
                # Complementar com busca semântica de favorecidos via embedding
                if busca_vetorial and len(dados_benef) < limit:
                    dados_sem = self._buscar_beneficiarios_semantico(
                        busca_vetorial, filtros_sql, db, limit
                    )
                    if dados_sem:
                        # Unir resultados sem duplicatas
                        ids_existentes = {d["id"] for d in dados_benef}
                        for d in dados_sem:
                            if d["id"] not in ids_existentes:
                                dados_benef.append(d)
                        logger.info("busca_beneficiario_complementada",
                                     total=len(dados_benef))
                return dados_benef[:limit]
            # Fallback: busca semântica de favorecidos
            if busca_vetorial:
                dados_sem = self._buscar_beneficiarios_semantico(
                    busca_vetorial, filtros_sql, db, limit
                )
                if dados_sem:
                    logger.info("busca_beneficiario_semantica", resultados=len(dados_sem))
                    return dados_sem[:limit]
            logger.info("busca_beneficiario_fallback", filtro=filtro_beneficiario)

        # Limite de candidatos para fusão RRF (buscar mais para ter material)
        fetch_limit = limit * settings.RRF_FETCH_MULTIPLIER

        # Busca SQL
        sql_limit = fetch_limit if estrategia == "rrf" else limit
        dados_sql = self.sql_search.construir_e_executar(filtros_sql, db, sql_limit)

        # Estratégia sql_only: retorna apenas SQL
        if estrategia == "sql_only":
            logger.info("busca_sql_only", resultados=len(dados_sql))
            return dados_sql[:limit]

        # Estratégia sql_first: vetor apenas se SQL insuficiente
        if estrategia == "sql_first":
            effective_threshold = sufficiency_threshold if sufficiency_threshold is not None else limit
            if not busca_vetorial or len(dados_sql) >= effective_threshold:
                logger.info("busca_sql_first_suficiente",
                             resultados=len(dados_sql), threshold=effective_threshold)
                return dados_sql[:limit]
            # SQL insuficiente — complementar com vetor e fusionar via RRF
            dados_vetoriais = self._combinar_vetoriais(
                busca_vetorial, db, fetch_limit, buscar_documentos
            )
            return self._fusionar_rrf(dados_sql, dados_vetoriais, limit)

        # Estratégia rrf (padrão): SEMPRE executar ambos e fusionar
        if not busca_vetorial:
            logger.warning("busca_rrf_sem_vetorial_fallback", resultados=len(dados_sql))
            return dados_sql[:limit]

        dados_vetoriais = self._combinar_vetoriais(
            busca_vetorial, db, fetch_limit, buscar_documentos
        )
        return self._fusionar_rrf(dados_sql, dados_vetoriais, limit)

    def _combinar_vetoriais(self, busca_vetorial: dict, db: Session,
                             fetch_limit: int, buscar_documentos: bool) -> List[dict]:
        """Combina resultados de busca vetorial em emendas e documentos.

        Quando buscar_documentos=True, busca também em documentos_emenda.embedding
        e combina os resultados, deduplicando por emenda_id e mantendo a maior
        similaridade.
        """
        dados_emendas = self.vector_search.buscar(busca_vetorial, db, fetch_limit)

        if not buscar_documentos:
            return dados_emendas

        dados_documentos = self.vector_search.buscar_documentos(
            busca_vetorial, db, fetch_limit
        )

        if not dados_documentos:
            return dados_emendas

        # Combinar: deduplicar por id, manter maior similaridade
        combined = {}
        for d in dados_emendas:
            combined[d["id"]] = d

        for d in dados_documentos:
            eid = d["id"]
            if eid not in combined or d.get("similaridade", 0) > combined[eid].get("similaridade", 0):
                combined[eid] = d

        result = sorted(combined.values(), key=lambda x: x.get("similaridade", 0), reverse=True)

        logger.info("vetorial_combinado",
                     emendas=len(dados_emendas),
                     documentos=len(dados_documentos),
                     combinado=len(result))
        return result

    def _buscar_beneficiarios_semantico(self, busca_vetorial: dict,
                                         filtros_sql: dict, db: Session,
                                         limit: int) -> List[dict]:
        """Busca beneficiários via similaridade semântica nos favorecidos.

        Encontra favorecidos semanticamente similares à consulta e depois
        busca emendas vinculadas a eles via documentos_emenda.
        """
        # Buscar favorecidos similares
        favorecidos = self.vector_search.buscar_favorecidos(
            busca_vetorial, db, limit=limit * 2
        )
        if not favorecidos:
            return []

        # Extrair CPF/CNPJs dos favorecidos encontrados
        cpf_cnpjs = [f["cpf_cnpj"] for f in favorecidos if f.get("cpf_cnpj")]
        if not cpf_cnpjs:
            return []

        # Buscar emendas vinculadas via documentos
        from sqlalchemy import text
        placeholders = ", ".join(f":cpf{i}" for i in range(len(cpf_cnpjs)))
        params = {f"cpf{i}": cpf for i, cpf in enumerate(cpf_cnpjs)}

        # Adicionar filtros SQL opcionais
        where_extra = ""
        if filtros_sql.get("uf"):
            where_extra += " AND e.uf = :uf"
            params["uf"] = filtros_sql["uf"]
        if filtros_sql.get("ano"):
            where_extra += " AND e.ano = :ano"
            params["ano"] = filtros_sql["ano"]
        if filtros_sql.get("funcao"):
            where_extra += " AND e.funcao = :funcao"
            params["funcao"] = filtros_sql["funcao"]

        params["limit"] = limit

        sql = f"""
            SELECT DISTINCT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor,
                   e.ano, e.tipo_emenda, e.funcao_nome, e.subfuncao_nome,
                   e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido,
                   df.favorecido_nome AS beneficiario_nome,
                   df.favorecido_cpf_cnpj AS beneficiario_cpf_cnpj
            FROM documentos_emenda df
            JOIN emendas e ON df.emenda_id = e.id
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE df.favorecido_cpf_cnpj IN ({placeholders})
              {where_extra}
            ORDER BY e.valor_pago DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("busca_beneficiario_semantico_sql",
                     favorecidos_encontrados=len(favorecidos),
                     emendas_vinculadas=len(rows))
        return rows
