from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import structlog

logger = structlog.get_logger()


class SQLSearchService:
    """Constrói e executa consultas SQL parametrizadas."""

    def _build_where(self, filtros: dict, params: dict,
                     alias_emenda: str = "e",
                     alias_parlamentar: str = "p") -> str:
        """Constrói cláusula WHERE a partir dos filtros."""
        where_clauses = []

        if "ano" in filtros:
            where_clauses.append(f"{alias_emenda}.ano = :ano")
            params["ano"] = filtros["ano"]
        if "ano_inicio" in filtros and "ano_fim" in filtros:
            where_clauses.append(
                f"{alias_emenda}.ano BETWEEN :ano_inicio AND :ano_fim")
            params["ano_inicio"] = filtros["ano_inicio"]
            params["ano_fim"] = filtros["ano_fim"]
        if "uf" in filtros:
            where_clauses.append(f"{alias_emenda}.uf = :uf")
            params["uf"] = filtros["uf"]
        if "ufs" in filtros and filtros["ufs"]:
            placeholders = ", ".join(
                f":uf_{i}" for i in range(len(filtros["ufs"])))
            where_clauses.append(f"{alias_emenda}.uf IN ({placeholders})")
            for i, uf in enumerate(filtros["ufs"]):
                params[f"uf_{i}"] = uf
        if "autor" in filtros:
            where_clauses.append(f"{alias_emenda}.nome_autor LIKE :autor")
            params["autor"] = f"%{filtros['autor']}%"
        if "autores" in filtros and filtros["autores"]:
            autor_conds = []
            for i, autor in enumerate(filtros["autores"]):
                autor_conds.append(f"{alias_emenda}.nome_autor LIKE :autor_{i}")
                params[f"autor_{i}"] = f"%{autor}%"
            where_clauses.append(f"({' OR '.join(autor_conds)})")
        if "partido" in filtros:
            where_clauses.append(f"{alias_parlamentar}.partido = :partido")
            params["partido"] = filtros["partido"]
        if "partidos" in filtros and filtros["partidos"]:
            placeholders = ", ".join(
                f":partido_{i}" for i in range(len(filtros["partidos"])))
            where_clauses.append(f"{alias_parlamentar}.partido IN ({placeholders})")
            for i, p in enumerate(filtros["partidos"]):
                params[f"partido_{i}"] = p
        if "funcao" in filtros:
            where_clauses.append(f"{alias_emenda}.funcao = :funcao")
            params["funcao"] = filtros["funcao"]
        if "funcoes" in filtros and filtros["funcoes"]:
            placeholders = ", ".join(
                f":funcao_{i}" for i in range(len(filtros["funcoes"])))
            where_clauses.append(f"{alias_emenda}.funcao IN ({placeholders})")
            for i, f in enumerate(filtros["funcoes"]):
                params[f"funcao_{i}"] = f
        if "subfuncao" in filtros:
            where_clauses.append(f"{alias_emenda}.subfuncao = :subfuncao")
            params["subfuncao"] = filtros["subfuncao"]
        if "subfuncoes" in filtros and filtros["subfuncoes"]:
            placeholders = ", ".join(
                f":subfuncao_{i}" for i in range(len(filtros["subfuncoes"])))
            where_clauses.append(
                f"{alias_emenda}.subfuncao IN ({placeholders})")
            for i, sf in enumerate(filtros["subfuncoes"]):
                params[f"subfuncao_{i}"] = sf
        if "tipo_emenda" in filtros:
            where_clauses.append(
                f"{alias_emenda}.tipo_emenda LIKE :tipo_emenda")
            params["tipo_emenda"] = f"%{filtros['tipo_emenda']}%"

        return " AND ".join(where_clauses) if where_clauses else "1=1"

    def construir_e_executar(self, filtros: dict, db: Session,
                              limit: int = 20) -> List[dict]:
        """Constrói SQL dinamicamente a partir dos filtros."""
        params = {"limit": limit}
        where = self._build_where(filtros, params)

        sql = f"""
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano,
                   e.tipo_emenda, e.funcao_nome, e.subfuncao_nome, e.uf,
                   e.localidade, e.valor_empenhado, e.valor_liquidado,
                   e.valor_pago, p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE {where}
            ORDER BY e.valor_empenhado DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]

        # Fallback: se sem resultados e filtro por funcao/subfuncao, buscar via documentos_emenda
        if not rows and ("funcao" in filtros or "subfuncao" in filtros
                         or "funcoes" in filtros or "subfuncoes" in filtros):
            rows = self._fallback_via_documentos(filtros, params, db, limit)

        logger.info("sql_executada", filtros=filtros, resultados=len(rows))
        return rows

    def _fallback_via_documentos(self, filtros: dict, params: dict,
                                  db: Session, limit: int) -> List[dict]:
        """Busca emendas cuja classificação aparece nos documentos_emenda."""
        doc_clauses = []
        doc_params = {"limit": limit}

        # Filtros na emenda (ano, uf, autor, etc.)
        if "ano" in filtros:
            doc_clauses.append("e.ano = :ano")
            doc_params["ano"] = filtros["ano"]
        if "ano_inicio" in filtros and "ano_fim" in filtros:
            doc_clauses.append("e.ano BETWEEN :ano_inicio AND :ano_fim")
            doc_params["ano_inicio"] = filtros["ano_inicio"]
            doc_params["ano_fim"] = filtros["ano_fim"]
        if "uf" in filtros:
            doc_clauses.append("e.uf = :uf")
            doc_params["uf"] = filtros["uf"]
        if "ufs" in filtros:
            ph = ", ".join(f":uf_{i}" for i in range(len(filtros["ufs"])))
            doc_clauses.append(f"e.uf IN ({ph})")
            for i, uf in enumerate(filtros["ufs"]):
                doc_params[f"uf_{i}"] = uf
        if "autor" in filtros:
            doc_clauses.append("e.nome_autor LIKE :autor")
            doc_params["autor"] = f"%{filtros['autor']}%"
        if "autores" in filtros and filtros["autores"]:
            autor_conds = []
            for i, autor in enumerate(filtros["autores"]):
                autor_conds.append(f"e.nome_autor LIKE :autor_{i}")
                doc_params[f"autor_{i}"] = f"%{autor}%"
            doc_clauses.append(f"({' OR '.join(autor_conds)})")
        if "partido" in filtros:
            doc_clauses.append("p.partido = :partido")
            doc_params["partido"] = filtros["partido"]
        if "partidos" in filtros and filtros["partidos"]:
            ph = ", ".join(f":partido_{i}" for i in range(len(filtros["partidos"])))
            doc_clauses.append(f"p.partido IN ({ph})")
            for i, p in enumerate(filtros["partidos"]):
                doc_params[f"partido_{i}"] = p

        # Filtro por funcao/subfuncao nos documentos (LIKE para formato "18 - Gestão ambiental")
        if "funcao" in filtros:
            doc_clauses.append("d.funcao LIKE :doc_funcao")
            doc_params["doc_funcao"] = f"{filtros['funcao']}%"
        if "subfuncao" in filtros:
            doc_clauses.append("d.subfuncao LIKE :doc_subfuncao")
            doc_params["doc_subfuncao"] = f"{filtros['subfuncao']}%"
        if "subfuncoes" in filtros and filtros["subfuncoes"]:
            likes = []
            for i, sf in enumerate(filtros["subfuncoes"]):
                likes.append(f"d.subfuncao LIKE :doc_subfuncao_{i}")
                doc_params[f"doc_subfuncao_{i}"] = f"{sf}%"
            doc_clauses.append(f"({' OR '.join(likes)})")
        if "funcoes" in filtros and filtros["funcoes"]:
            likes = []
            for i, f in enumerate(filtros["funcoes"]):
                likes.append(f"d.funcao LIKE :doc_funcao_{i}")
                doc_params[f"doc_funcao_{i}"] = f"{f}%"
            doc_clauses.append(f"({' OR '.join(likes)})")

        where = " AND ".join(doc_clauses) if doc_clauses else "1=1"

        sql = f"""
            SELECT DISTINCT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor,
                   e.ano, e.tipo_emenda, e.funcao_nome, e.subfuncao_nome,
                   e.uf, e.localidade, e.valor_empenhado, e.valor_liquidado,
                   e.valor_pago, p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            INNER JOIN documentos_emenda d ON d.emenda_id = e.id
            WHERE {where}
            ORDER BY e.valor_empenhado DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), doc_params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        if rows:
            logger.info("fallback_documentos", filtros=filtros, resultados=len(rows))
        return rows

    @staticmethod
    def _normalizar_texto(texto: str) -> str:
        """Remove acentos e converte para maiúsculas para busca."""
        import unicodedata
        nfkd = unicodedata.normalize("NFKD", texto)
        sem_acento = "".join(c for c in nfkd if not unicodedata.combining(c))
        return sem_acento.upper()

    def buscar_por_beneficiario(self, filtro_beneficiario: str,
                                 filtros: dict, db: Session,
                                 limit: int = 20) -> List[dict]:
        """Busca emendas por nome de beneficiário usando tabela normalizada."""
        benef_norm = self._normalizar_texto(filtro_beneficiario)
        where_clauses = ["UPPER(f.nome) LIKE :benef_nome"]
        params = {"benef_nome": f"%{benef_norm}%", "limit": limit}

        if "ano" in filtros:
            where_clauses.append("e.ano = :ano")
            params["ano"] = filtros["ano"]
        if "ano_inicio" in filtros and "ano_fim" in filtros:
            where_clauses.append("e.ano BETWEEN :ano_inicio AND :ano_fim")
            params["ano_inicio"] = filtros["ano_inicio"]
            params["ano_fim"] = filtros["ano_fim"]
        if "uf" in filtros:
            where_clauses.append("e.uf = :uf")
            params["uf"] = filtros["uf"]
        if "ufs" in filtros:
            placeholders = ", ".join(
                f":uf_{i}" for i in range(len(filtros["ufs"])))
            where_clauses.append(f"e.uf IN ({placeholders})")
            for i, uf in enumerate(filtros["ufs"]):
                params[f"uf_{i}"] = uf
        if "funcao" in filtros:
            where_clauses.append("e.funcao = :funcao")
            params["funcao"] = filtros["funcao"]
        if "partido" in filtros:
            where_clauses.append("p.partido = :partido")
            params["partido"] = filtros["partido"]

        where = " AND ".join(where_clauses)

        sql = f"""
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano,
                   e.tipo_emenda, e.funcao_nome, e.subfuncao_nome, e.uf,
                   e.localidade, e.valor_empenhado, e.valor_liquidado,
                   e.valor_pago, p.partido,
                   f.nome AS beneficiario_nome,
                   f.cpf_cnpj AS beneficiario_cpf_cnpj,
                   f.tipo_pessoa AS beneficiario_tipo,
                   df.valor_recebido AS beneficiario_valor
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            INNER JOIN documentos_emenda d ON d.emenda_id = e.id
            INNER JOIN documento_favorecido df ON df.documento_id = d.id
            INNER JOIN favorecidos f ON f.id = df.favorecido_id
            WHERE {where}
            ORDER BY df.valor_recebido DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("sql_beneficiario_executada",
                     beneficiario=filtro_beneficiario, resultados=len(rows))
        return rows

    def construir_agregacao(self, filtros: dict, operacao: str,
                             db: Session, limit: int = 20) -> List[dict]:
        """Constrói queries com SUM/COUNT/AVG + GROUP BY."""
        params = {"limit": limit}
        where = self._build_where(filtros, params)

        if operacao == "soma":
            sql = f"""
                SELECT SUM(e.valor_empenhado) AS total_empenhado,
                       SUM(e.valor_liquidado) AS total_liquidado,
                       SUM(e.valor_pago) AS total_pago,
                       COUNT(*) AS quantidade
                FROM emendas e
                LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
                WHERE {where}
            """
        elif operacao == "contagem":
            sql = f"""
                SELECT COUNT(*) AS quantidade
                FROM emendas e
                LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
                WHERE {where}
            """
        elif operacao == "media":
            sql = f"""
                SELECT AVG(e.valor_empenhado) AS media_empenhado,
                       AVG(e.valor_pago) AS media_pago,
                       COUNT(*) AS quantidade
                FROM emendas e
                LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
                WHERE {where}
            """
        elif operacao == "ranking":
            # Ranking por autor
            sql = f"""
                SELECT e.nome_autor, p.partido, e.uf,
                       SUM(e.valor_empenhado) AS total_empenhado,
                       SUM(e.valor_pago) AS total_pago,
                       COUNT(*) AS quantidade
                FROM emendas e
                LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
                WHERE {where}
                GROUP BY e.nome_autor, p.partido, e.uf
                ORDER BY total_empenhado DESC
                LIMIT :limit
            """
        else:
            return self.construir_e_executar(filtros, db, limit)

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("sql_agregacao_executada", operacao=operacao,
                     filtros=filtros, resultados=len(rows))
        return rows

    def contar_total(self, filtros: dict, db: Session) -> int:
        """Retorna o total de registros que atendem aos filtros (sem LIMIT)."""
        params = {}
        where = self._build_where(filtros, params)
        sql = f"""
            SELECT COUNT(*) FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE {where}
        """
        result = db.execute(text(sql), params)
        return result.scalar() or 0

    def verificar_sancoes(self, cpf_cnpj: str, db: Session) -> List[dict]:
        """Verifica se um CPF/CNPJ consta em cadastros de sanções."""
        sancoes = []

        # CEIS
        result = db.execute(text(
            "SELECT nome, tipo_sancao, orgao_sancionador, data_inicio, data_fim "
            "FROM sancoes_ceis WHERE cpf_cnpj = :cpf"
        ), {"cpf": cpf_cnpj})
        for row in result.fetchall():
            sancoes.append({
                "cadastro": "CEIS",
                "nome": row[0], "tipo": row[1],
                "orgao": row[2], "inicio": str(row[3] or ""),
                "fim": str(row[4] or ""),
            })

        # CNEP
        result = db.execute(text(
            "SELECT nome, tipo_sancao, orgao_sancionador, data_inicio, data_fim "
            "FROM sancoes_cnep WHERE cpf_cnpj = :cpf"
        ), {"cpf": cpf_cnpj})
        for row in result.fetchall():
            sancoes.append({
                "cadastro": "CNEP",
                "nome": row[0], "tipo": row[1],
                "orgao": row[2], "inicio": str(row[3] or ""),
                "fim": str(row[4] or ""),
            })

        # CEPIM (usa cnpj)
        result = db.execute(text(
            "SELECT nome, motivo, orgao_maximo "
            "FROM sancoes_cepim WHERE cnpj = :cpf"
        ), {"cpf": cpf_cnpj})
        for row in result.fetchall():
            sancoes.append({
                "cadastro": "CEPIM",
                "nome": row[0], "tipo": row[1], "orgao": row[2],
                "inicio": "", "fim": "",
            })

        # CEAF (usa cpf)
        result = db.execute(text(
            "SELECT nome, tipo_punicao, orgao_lotacao, data_inicio, data_fim "
            "FROM sancoes_ceaf WHERE cpf = :cpf"
        ), {"cpf": cpf_cnpj})
        for row in result.fetchall():
            sancoes.append({
                "cadastro": "CEAF",
                "nome": row[0], "tipo": row[1],
                "orgao": row[2], "inicio": str(row[3] or ""),
                "fim": str(row[4] or ""),
            })

        if sancoes:
            logger.info("sancoes_encontradas", cpf_cnpj=cpf_cnpj[:8] + "...",
                         total=len(sancoes))
        return sancoes

    def listar_beneficiarios_emenda(self, codigo_emenda: str,
                                      db: Session) -> List[dict]:
        """Lista todos os beneficiários de uma emenda específica."""
        sql = """
            SELECT f.nome, f.cpf_cnpj, f.tipo_pessoa, df.valor_recebido,
                   d.fase, d.valor AS valor_documento, d.data_documento
            FROM favorecidos f
            INNER JOIN documento_favorecido df ON df.favorecido_id = f.id
            INNER JOIN documentos_emenda d ON df.documento_id = d.id
            INNER JOIN emendas e ON d.emenda_id = e.id
            WHERE e.codigo_emenda = :codigo
            ORDER BY df.valor_recebido DESC
        """

        result = db.execute(text(sql), {"codigo": codigo_emenda})
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("beneficiarios_emenda", codigo=codigo_emenda, total=len(rows))
        return rows
