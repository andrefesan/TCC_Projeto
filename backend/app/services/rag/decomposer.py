from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import numpy as np
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
            autor = entidades["autor"]
            if isinstance(autor, list):
                filtros_sql["autores"] = [a.upper() if isinstance(a, str) else str(a).upper() for a in autor]
            else:
                filtros_sql["autor"] = autor.upper()
        if entidades.get("partido"):
            partido = entidades["partido"]
            if isinstance(partido, list):
                filtros_sql["partidos"] = [p.upper() if isinstance(p, str) else str(p).upper() for p in partido]
            else:
                filtros_sql["partido"] = partido.upper()
        if entidades.get("tipo_emenda"):
            filtros_sql["tipo_emenda"] = entidades["tipo_emenda"]

        # Campo semântico: banco → sinônimos → vetorial
        if entidades.get("area"):
            area_raw = entidades["area"]
            # Comparativas podem retornar lista de áreas
            if isinstance(area_raw, list):
                areas = [a.lower().strip() for a in area_raw if isinstance(a, str)]
            else:
                area_single = area_raw.lower().strip()
                areas = [area_single] if area_single else []

            codigos_funcao = []
            codigos_subfuncao = []
            for area in areas:
                codigo = self._resolver_area_via_banco(area, db)
                if codigo:
                    if len(codigo) <= 2:
                        codigos_funcao.append(codigo)
                    else:
                        codigos_subfuncao.append(codigo)
                    logger.info("area_resolvida", area=area, codigo=codigo)
                else:
                    # Último fallback: busca vetorial na classificação orçamentária
                    embedding = self.embedder.encode(area)
                    codigo = self._busca_vetorial_classificacao(embedding, db)
                    if codigo:
                        codigos_funcao.append(codigo)
                        logger.info("area_resolvida_vetorial", area=area, codigo=codigo)
                    else:
                        # Enriquecer embedding com contexto da consulta (UF, ano)
                        texto_busca = area
                        if entidades.get("uf"):
                            texto_busca += f" {entidades['uf']}"
                        if entidades.get("ano"):
                            texto_busca += f" {entidades['ano']}"
                        embedding_enriquecido = self.embedder.encode(texto_busca)
                        busca_vetorial = {"termo": texto_busca, "embedding": embedding_enriquecido.tolist()}
                        logger.warning("area_nao_resolvida", area=area, texto_busca=texto_busca)

            # Atribuir filtros: usar OR (funcao OU subfuncoes típicas) para
            # capturar subfunções atípicas (ex: policiamento sob outra função)
            if len(codigos_funcao) == 1 and not codigos_subfuncao:
                sf_tipicas = self.dicionario.obter_subfuncoes_tipicas(codigos_funcao[0])
                if sf_tipicas:
                    filtros_sql["funcao_ou_subfuncoes"] = {
                        "funcao": codigos_funcao[0],
                        "subfuncoes": sf_tipicas,
                    }
                    logger.info("filtro_or_funcao_subfuncoes",
                                funcao=codigos_funcao[0], subfuncoes=sf_tipicas)
                else:
                    filtros_sql["funcao"] = codigos_funcao[0]
            elif len(codigos_funcao) > 1:
                filtros_sql["funcoes"] = codigos_funcao
            if codigos_subfuncao and "funcao_ou_subfuncoes" not in filtros_sql:
                if len(codigos_subfuncao) == 1:
                    filtros_sql["subfuncao"] = codigos_subfuncao[0]
                else:
                    filtros_sql["subfuncoes"] = codigos_subfuncao

        # Filtros de beneficiário
        busca_beneficiario = entidades.get("busca_beneficiario", False)
        filtro_beneficiario = None
        if entidades.get("beneficiario"):
            filtro_beneficiario = entidades["beneficiario"]
            busca_beneficiario = True
        if entidades.get("instituicao") and not filtro_beneficiario:
            filtro_beneficiario = entidades["instituicao"]
            busca_beneficiario = True

        # Operação (busca, soma, ranking, contagem, media)
        operacao = entidades.get("operacao", "busca")
        operacao_map = {
            "total": "soma", "quanto": "soma", "valor total": "soma",
            "quantas": "contagem", "quantos": "contagem", "número": "contagem",
            "contagem_distinta": "contagem",
            "maiores": "ranking", "top": "ranking", "quem mais": "ranking",
            "média": "media", "em média": "media",
            "comparação": "busca", "comparacao": "busca",
            "tendência": "busca", "tendencia": "busca",
        }
        operacao = operacao_map.get(operacao.lower(), operacao.lower())
        if operacao not in ("busca", "soma", "contagem", "ranking", "media"):
            operacao = "busca"

        return {
            "filtros_sql": filtros_sql,
            "busca_vetorial": busca_vetorial,
            "operacao": operacao,
            "busca_beneficiario": busca_beneficiario,
            "filtro_beneficiario": filtro_beneficiario,
        }

    def _resolver_area_via_banco(self, area: str, db: Session) -> str | None:
        """Resolve área via dicionário, funções e subfunções normalizadas."""
        # 1. Dicionário semântico (sinônimos curados manualmente — prioridade máxima)
        codigo_dict = self.dicionario.resolver_area(area)
        if codigo_dict:
            return codigo_dict

        # 2. Busca em subfuncoes primeiro (mais específico — termos como "educação básica")
        try:
            row = db.execute(text(
                "SELECT codigo FROM subfuncoes WHERE LOWER(nome) LIKE :t LIMIT 1"
            ), {"t": f"%{area}%"}).fetchone()
            if row:
                return row[0]
        except Exception:
            pass

        # 3. Busca em funcoes depois (mais abrangente — termos genéricos como "educação")
        try:
            row = db.execute(text(
                "SELECT codigo FROM funcoes WHERE LOWER(nome) LIKE :t LIMIT 1"
            ), {"t": f"%{area}%"}).fetchone()
            if row:
                return row[0]
        except Exception:
            pass

        return None

    _NOMES_UF = {
        "acre": "AC", "alagoas": "AL", "amapa": "AP", "amazonas": "AM",
        "bahia": "BA", "ceara": "CE", "distrito federal": "DF",
        "espirito santo": "ES", "goias": "GO", "maranhao": "MA",
        "mato grosso": "MT", "mato grosso do sul": "MS",
        "minas gerais": "MG", "para": "PA", "paraiba": "PB",
        "parana": "PR", "pernambuco": "PE", "piaui": "PI",
        "rio de janeiro": "RJ", "rio grande do norte": "RN",
        "rio grande do sul": "RS", "rondonia": "RO", "roraima": "RR",
        "santa catarina": "SC", "sao paulo": "SP", "sergipe": "SE",
        "tocantins": "TO",
    }

    def _resolver_uf(self, uf_raw) -> str | list:
        """Resolve UF ou região para sigla(s)."""
        # Se o LLM retornou uma lista (consultas comparativas), resolver cada uma
        if isinstance(uf_raw, list):
            resultado = []
            for item in uf_raw:
                resolvido = self._resolver_uf(item)
                if isinstance(resolvido, list):
                    resultado.extend(resolvido)
                else:
                    resultado.append(resolvido)
            return resultado
        regioes = self.dicionario.resolver_regiao(uf_raw)
        if regioes:
            return regioes
        # Tenta resolver nome completo do estado
        import unicodedata
        nome_norm = unicodedata.normalize("NFKD", str(uf_raw).lower().strip())
        nome_norm = "".join(c for c in nome_norm if not unicodedata.combining(c))
        if nome_norm in self._NOMES_UF:
            return self._NOMES_UF[nome_norm]
        # Se já é sigla de 2 caracteres, retorna diretamente
        if len(str(uf_raw).strip()) == 2:
            return str(uf_raw).upper().strip()
        return str(uf_raw).upper()[:2]

    def _busca_vetorial_classificacao(self, embedding, db: Session) -> str | None:
        """Busca classificação mais similar por embedding."""
        is_sqlite = "sqlite" in str(db.bind.url)

        if is_sqlite:
            return self._busca_vetorial_classificacao_sqlite(embedding, db)

        result = db.execute(text("""
            SELECT funcao, 1 - (embedding <=> CAST(:emb AS vector)) AS similaridade
            FROM classificacao_orcamentaria
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> CAST(:emb AS vector)
            LIMIT 1
        """), {"emb": str(embedding.tolist())})
        row = result.fetchone()
        if row and row.similaridade >= settings.SIMILARITY_THRESHOLD:
            return row.funcao
        return None

    def _busca_vetorial_classificacao_sqlite(self, embedding, db: Session) -> str | None:
        """Busca classificação por cosine similarity em Python (SQLite)."""
        query_emb = np.array(embedding.tolist() if hasattr(embedding, 'tolist') else embedding, dtype=np.float32)
        result = db.execute(text("""
            SELECT funcao, embedding FROM classificacao_orcamentaria
            WHERE embedding IS NOT NULL
        """))
        best_funcao = None
        best_sim = -1.0
        for row in result.fetchall():
            try:
                emb = np.array(json.loads(row.embedding), dtype=np.float32)
            except (json.JSONDecodeError, TypeError):
                continue
            sim = float(np.dot(query_emb, emb) / (
                np.linalg.norm(query_emb) * np.linalg.norm(emb) + 1e-10
            ))
            if sim > best_sim:
                best_sim = sim
                best_funcao = row.funcao
        if best_sim >= settings.SIMILARITY_THRESHOLD:
            return best_funcao
        return None
