from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import structlog

logger = structlog.get_logger()


class SQLSearchService:
    """Constrói e executa consultas SQL parametrizadas."""

    def construir_e_executar(self, filtros: dict, db: Session,
                              limit: int = 20) -> List[dict]:
        """Constrói SQL dinamicamente a partir dos filtros."""
        where_clauses = []
        params = {"limit": limit}

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
            placeholders = ", ".join(f":uf_{i}" for i in range(len(filtros["ufs"])))
            where_clauses.append(f"e.uf IN ({placeholders})")
            for i, uf in enumerate(filtros["ufs"]):
                params[f"uf_{i}"] = uf
        if "autor" in filtros:
            where_clauses.append("e.nome_autor LIKE :autor")
            params["autor"] = f"%{filtros['autor']}%"
        if "partido" in filtros:
            where_clauses.append("p.partido = :partido")
            params["partido"] = filtros["partido"]
        if "funcao" in filtros:
            where_clauses.append("e.funcao = :funcao")
            params["funcao"] = filtros["funcao"]
        if "subfuncao" in filtros:
            where_clauses.append("e.subfuncao = :subfuncao")
            params["subfuncao"] = filtros["subfuncao"]
        if "tipo_emenda" in filtros:
            where_clauses.append("e.tipo_emenda LIKE :tipo_emenda")
            params["tipo_emenda"] = f"%{filtros['tipo_emenda']}%"

        where = " AND ".join(where_clauses) if where_clauses else "TRUE"

        sql = f"""
            SELECT e.id, e.codigo_emenda, e.cod_autor, e.nome_autor, e.ano, e.tipo_emenda,
                   e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            WHERE {where}
            ORDER BY e.valor_empenhado DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("sql_executada", filtros=filtros, resultados=len(rows))
        return rows

    def buscar_por_beneficiario(self, filtro_beneficiario: str,
                                 filtros: dict, db: Session,
                                 limit: int = 20) -> List[dict]:
        """Busca emendas por nome de beneficiário com JOINs nas tabelas de documentos."""
        where_clauses = ["b.nome LIKE :benef_nome"]
        params = {"benef_nome": f"%{filtro_beneficiario}%", "limit": limit}

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
            placeholders = ", ".join(f":uf_{i}" for i in range(len(filtros["ufs"])))
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
                   e.tipo_emenda, e.funcao_nome, e.subfuncao_nome, e.uf, e.localidade,
                   e.valor_empenhado, e.valor_liquidado, e.valor_pago,
                   p.partido,
                   b.nome AS beneficiario_nome,
                   b.cpf_cnpj AS beneficiario_cpf_cnpj,
                   b.tipo_pessoa AS beneficiario_tipo,
                   b.valor_recebido AS beneficiario_valor
            FROM emendas e
            LEFT JOIN parlamentares p ON e.cod_autor = p.cod_autor
            INNER JOIN documentos_emenda d ON d.emenda_id = e.id
            INNER JOIN beneficiarios b ON b.documento_id = d.id
            WHERE {where}
            ORDER BY b.valor_recebido DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("sql_beneficiario_executada",
                     beneficiario=filtro_beneficiario, resultados=len(rows))
        return rows

    def listar_beneficiarios_emenda(self, codigo_emenda: str,
                                      db: Session) -> List[dict]:
        """Lista todos os beneficiários de uma emenda específica."""
        sql = """
            SELECT b.nome, b.cpf_cnpj, b.tipo_pessoa, b.valor_recebido,
                   d.fase, d.valor AS valor_documento, d.data_documento
            FROM beneficiarios b
            INNER JOIN documentos_emenda d ON b.documento_id = d.id
            INNER JOIN emendas e ON d.emenda_id = e.id
            WHERE e.codigo_emenda = :codigo
            ORDER BY b.valor_recebido DESC
        """

        result = db.execute(text(sql), {"codigo": codigo_emenda})
        rows = [dict(r._mapping) for r in result.fetchall()]
        logger.info("beneficiarios_emenda", codigo=codigo_emenda, total=len(rows))
        return rows
